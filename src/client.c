/**
 * Runs on the client and sends messages to the detour kernel module.
 * build: make netlink_client
 * run: ./netlink_client CMD [ARGS ...]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include <netlink/netlink.h>
#include <netlink/attr.h>
#include <netlink/handlers.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>

/**
 * How many calls should the DETOUR_C_REQ echo handler listen to before quit?
 */
#define MAX_CALLS 5

/**
 * Format for UDP mproxy requests.
 */
struct mproxy_request {
	uint8_t ver;
	uint8_t op;
	uint8_t _reserved[2];
	uint32_t rip;
	uint16_t rpt;
	uint16_t dpt;
};

/**
 * MProxy protocol definitions.
 */
#define MPROXY_VERSION 1
#define MPROXY_REQUEST 0
#define MPROXY_RESPONSE 1

/**
 * UDP socket to send requests to. Should be connect()-ed so all you need to do
 * is send(), not sendto().
 */
int mproxy_sk;

/**
 * address of mproxy daemon
 */
struct sockaddr_in mproxy_addr;

/**
 * netlink family
 */
int family;

/**
 * netlink group
 */
int group;

/**
 * What port is the detour listening on? Should be this.
 */
#define MPROXY_DEFAULT_PORT htons(45672)

/**
 * The following are shamelessly taken from the kernel code.
 */
#define DETOUR_FAMILY "DETOUR"
#define DETOUR_GROUP "detour_req"
#define DETOUR_VERSION 1
enum {
	DETOUR_C_UNSPEC,
	DETOUR_C_ECHO,   // testing
	DETOUR_C_ADD,    // add detour route
	DETOUR_C_DEL,    // delete detour route
	DETOUR_C_REQ,    // request a detour route
	DETOUR_C_STAT,   // give stats on a detour
};
enum {
	DETOUR_A_UNSPEC,
	DETOUR_A_DETOUR_IP,
	DETOUR_A_DETOUR_PORT,
	DETOUR_A_REMOTE_IP,
	DETOUR_A_REMOTE_PORT,
	__DETOUR_A_MAX,
};
#define DETOUR_A_MAX (__DETOUR_A_MAX - 1)
static struct nla_policy detour_genl_policy[DETOUR_A_MAX + 1] = {
	[DETOUR_A_DETOUR_IP] = { .type = NLA_U32 },
	[DETOUR_A_DETOUR_PORT] = { .type = NLA_U16 },
	[DETOUR_A_REMOTE_IP] = { .type = NLA_U32 },
	[DETOUR_A_REMOTE_PORT] = { .type = NLA_U16 },
};


/**
 * Call the DETUOR_C_ECHO function in the kernel. The function itself takes no
 * arguments, but we do need a socket to send on.
 * @param sk A socket, which has already been initialized and connected
 * @retval zero on success, nonzero on failure
 */
int detour_echo(struct nl_sock *sk)
{
	int rc = -1;
	struct nl_msg *msg = nlmsg_alloc();
	if (!msg) {
		fprintf(stderr, "nlmsg_alloc failed\n");
		goto nla_put_failure;
	}

	if (!genlmsg_put(msg, NL_AUTO_PORT, NL_AUTO_SEQ, family, 0, 0,
	                 DETOUR_C_ECHO, DETOUR_VERSION)) {
		fprintf(stderr, "genlmsg_put() failed\n");
		goto nla_put_failure;
	}

	rc = nl_send_sync(sk, msg);
	if (rc)
		fprintf(stderr, "nl_send_sync failed: %d\n", rc);

nla_put_failure: // needed by NLA_PUT_X macros
	return rc;
}

/**
 * Call the DETOUR_C_ADD or DETOUR_C_DEL command with a NAT-based detour. This
 * means you'll need to specify detour and remote IP and port. You'll also need
 * to specify one of the two commands.
 */
int detour_add_or_del(struct nl_sock *sk, struct in_addr *dip,
                      uint16_t dpt, struct in_addr *rip, uint16_t rpt,
                      int command) {
	int rc = -1;
	struct nl_msg *msg = nlmsg_alloc();

	if (!msg) {
		fprintf(stderr, "nlmsg_alloc failed\n");
		goto nla_put_failure;
	}

	if (!genlmsg_put(msg, NL_AUTO_PORT, NL_AUTO_SEQ, family, 0, 0,
	                 command, DETOUR_VERSION)) {
		fprintf(stderr, "failed to put genl header\n");
		goto nla_put_failure;
	}
	NLA_PUT_U32(msg, DETOUR_A_DETOUR_IP, dip->s_addr);
	NLA_PUT_U16(msg, DETOUR_A_DETOUR_PORT, dpt);
	NLA_PUT_U32(msg, DETOUR_A_REMOTE_IP, rip->s_addr);
	NLA_PUT_U16(msg, DETOUR_A_REMOTE_PORT, rpt);

	rc = nl_send_sync(sk, msg);
	if (rc) {
		nl_perror(rc, "nl_send_sync");
	}

nla_put_failure:
	return rc;
}

/**
 * Callback function for DETOUR_C_REQ messages. Parses the message and then
 * echoes it to stdout.
 */
int detour_req_echo_cb(struct nl_msg *msg, void *arg)
{
	(void)arg;
	struct nlattr *attrs[DETOUR_A_MAX + 1];
	struct nlmsghdr *nlh = nlmsg_hdr(msg);
	struct in_addr rip;
	unsigned short rpt;
	int rc = genlmsg_parse(nlh, 0, attrs, DETOUR_A_MAX, detour_genl_policy);
	if (rc < 0) {
		fprintf(stderr, "genlmsg_parse() failed (%d)\n", rc);
		return NL_STOP;
	}
	if (!attrs[DETOUR_A_REMOTE_IP] || !attrs[DETOUR_A_REMOTE_PORT]) {
		fprintf(stderr, "did not receive all necessary attributes\n");
		return NL_STOP;
	}
	rip.s_addr = nla_get_u32(attrs[DETOUR_A_REMOTE_IP]);
	rpt = nla_get_u16(attrs[DETOUR_A_REMOTE_PORT]);
	rpt = ntohs(rpt);
	printf("DETOUR_C_REQ: %s:%u\n", inet_ntoa(rip), rpt);
	return NL_STOP;
}

/**
 * Callback function for DETOUR_C_REQ messages. Parses the message, requests a
 * detour via UDP, and then informs the kernel of the new detour.
 */
int detour_req_create_cb(struct nl_msg *msg, void *arg)
{
	struct nlattr *attrs[DETOUR_A_MAX + 1];
	struct nlmsghdr *nlh = nlmsg_hdr(msg);
	struct mproxy_request req, rsp;
	struct nl_sock *nl_sk = arg;
	int sk;
	int rc = genlmsg_parse(nlh, 0, attrs, DETOUR_A_MAX, detour_genl_policy);
	if (rc < 0) {
		nl_perror(rc, "genlmsg_parse");
		return NL_STOP;
	}
	if (!attrs[DETOUR_A_REMOTE_IP] || !attrs[DETOUR_A_REMOTE_PORT]) {
		fprintf(stderr, "did not receive all necessary attributes\n");
		return NL_STOP;
	}
	req.ver = MPROXY_VERSION;
	req.op = MPROXY_REQUEST;
	req._reserved[0] = 0;
	req._reserved[1] = 0;
	req.rip = nla_get_u32(attrs[DETOUR_A_REMOTE_IP]);
	req.rpt = nla_get_u16(attrs[DETOUR_A_REMOTE_PORT]);
	req.dpt = req.rpt;

	if (send(mproxy_sk, &req, sizeof(req), 0) != sizeof(req)) {
		perror("failed to send mproxy request");
		return NL_STOP;
	}

	if (recv(mproxy_sk, &req, sizeof(req), 0) != sizeof(req)) {
		perror("failed to recv mproxy resopnse");
		return NL_STOP;
	}

	detour_add_or_del(nl_sk, &mproxy_addr.sin_addr, req.dpt,
	                  (struct in_addr*)&req.rip, req.rpt,
	                  DETOUR_C_ADD);
	return NL_STOP;
}

/** Call DETOUR_C_ECHO, either using CLI provided string or a default. */
int cli_echo(struct nl_sock *sk, int argc, char *argv[])
{
	return detour_echo(sk);
}

/** Call DETOUR_C_ADD, using arguments from CLI. */
int cli_add_or_del(struct nl_sock *sk, int argc, char *argv[], uint8_t cmd)
{
	struct in_addr dip, rip;
	uint16_t dpt, rpt;
	if (argc != 6) {
		fprintf(stderr, "add requires 4 arguments\n");
		fprintf(stderr, "%s %s DIP DPT RIP RPT", argv[0], argv[1]);
		return -1;
	}
	if (!inet_aton(argv[2], &dip) || !inet_aton(argv[4], &rip)) {
		fprintf(stderr, "\"%s\" or \"%s\" is not a valid IP\n", argv[2],
			argv[4]);
		return -1;
	}
	if (1 != sscanf(argv[3], "%hu", &dpt)) {
		fprintf(stderr, "\"%s\" is not a valid port\n", argv[3]);
		return -1;
	}
	if (1 != sscanf(argv[5], "%hu", &rpt)) {
		fprintf(stderr, "\"%s\" is not a valid port\n", argv[5]);
		return -1;
	}
	return detour_add_or_del(sk, &dip, htons(dpt), &rip, htons(rpt), cmd);
}

/** Loop waiting for DETOUR_C_REQ messages from the kernel and print them. */
int cli_req(struct nl_sock *sk)
{
	int rc, calls = 0;
	rc = nl_socket_add_memberships(sk, group, NFNLGRP_NONE);
	if (rc < 0) {
		nl_perror(rc, "nl_socket_add_memberships");
		return rc;
	}
	rc = nl_socket_modify_cb(sk, NL_CB_MSG_IN, NL_CB_CUSTOM,
	                         detour_req_echo_cb, NULL);
	if (rc < 0) {
		nl_perror(rc, "nl_cb_set");
		return rc;
	}
	nl_socket_disable_seq_check(sk);
	do {
		rc = nl_recvmsgs_default(sk);
	} while (++calls < MAX_CALLS && rc >= 0);
	if (rc < 0) {
		nl_perror(rc, "nl_recvmsgs");
	}
	return rc;
}

/**
 * Daemon-mode for cli. This is the "main point" of this client: wait for detour
 * requests from the kernel, send them to our detour server, and inform the
 * kernel of the newly available detours.
 */
int cli_daemon(struct nl_sock *sk, int argc, char *argv[])
{
	int rc;
	/* get detour address and create socket */
	if (argc < 3) {
		fprintf(stderr, "expected detour ip address\n");
		return EXIT_FAILURE;
	}
	mproxy_addr.sin_family = AF_INET;
	if (!inet_aton(argv[2], &mproxy_addr.sin_addr)) {
		fprintf(stderr, "invalid detour ip address\n");
		return EXIT_FAILURE;
	}
	mproxy_addr.sin_port = MPROXY_DEFAULT_PORT;
	mproxy_sk = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	if (mproxy_sk == -1) {
		perror("socket");
		return EXIT_FAILURE;
	}
	if (connect(mproxy_sk, (struct sockaddr*)&mproxy_addr,
	            sizeof(mproxy_addr)) == -1) {
		perror("connect");
		return EXIT_FAILURE;
	}
	/* Setup netlink callback and group membership for receiving */
	rc = nl_socket_add_memberships(sk, group, NFNLGRP_NONE);
	if (rc < 0) {
		nl_perror(rc, "nl_socket_add_memberships");
		return rc;
	}
	rc = nl_socket_modify_cb(sk, NL_CB_MSG_IN, NL_CB_CUSTOM,
	                         detour_req_create_cb, sk);
	if (rc < 0) {
		nl_perror(rc, "nl_cb_set");
		return rc;
	}
	nl_socket_disable_seq_check(sk);
	/* now we loop receiving netlink messages */
	do {
		rc = nl_recvmsgs_default(sk);
	} while (rc >= 0);
	if (rc < 0) {
		nl_perror(rc, "nl_recvmsgs");
	}
	return rc;
}

/**
 * Parses first argument and invokes the correct cli_ function.
 */
int main(int argc, char *argv[])
{
	struct nl_sock *sk;
	int rc = EXIT_SUCCESS;

	if (argc < 2) {
		fprintf(stderr, "expected at least one argument\n");
		return EXIT_FAILURE;
	}

	sk = nl_socket_alloc();
	if (!sk) {
		nl_perror(rc, "nl_socket_alloc");
		rc = EXIT_FAILURE;
		goto exit;
	}
	rc = genl_connect(sk);
	if (rc != 0) {
		nl_perror(rc, "genl_connect");
		rc = EXIT_FAILURE;
		goto exit;
	}

	family = genl_ctrl_resolve(sk, DETOUR_FAMILY);
	if (family < 0) {
		nl_perror(family, "genl_ctrl_resolve");
		rc = EXIT_FAILURE;
		goto exit;
	}

	group = genl_ctrl_resolve_grp(sk, DETOUR_FAMILY, DETOUR_GROUP);
	if (group < 0) {
		nl_perror(group, "genl_ctrl_resolve_grp");
		rc = EXIT_FAILURE;
		goto exit;
	}

	if (strcmp(argv[1], "echo") == 0) {
		rc = cli_echo(sk, argc, argv);
	} else if (strcmp(argv[1], "add") == 0) {
		rc = cli_add_or_del(sk, argc, argv, DETOUR_C_ADD);
	} else if (strcmp(argv[1], "del") == 0) {
		rc = cli_add_or_del(sk, argc, argv, DETOUR_C_DEL);
	} else if (strcmp(argv[1], "req") == 0) {
		rc = cli_req(sk);
	} else if (strcmp(argv[1], "daemon") == 0) {
		rc = cli_daemon(sk, argc, argv);
	} else {
		fprintf(stderr, "\"%s\" is not a valid command\n", argv[1]);
		rc = EXIT_FAILURE;
	}

exit:
	nl_socket_free(sk);
	return rc;
}
