/*
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
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>

/*
 * The following are shamelessly taken from the kernel code.
 */
#define DETOUR_FAMILY "DETOUR"
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
	DETOUR_A_MSG,
	DETOUR_A_DETOUR_IP,
	DETOUR_A_DETOUR_PORT,
	DETOUR_A_REMOTE_IP,
	DETOUR_A_REMOTE_PORT,
};

int detour_echo(struct nl_sock *sk, int family, char *text)
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
	NLA_PUT_STRING(msg, DETOUR_A_MSG, text);

	rc = nl_send_sync(sk, msg);
	if (rc)
		fprintf(stderr, "nl_send_sync failed: %d\n", rc);

nla_put_failure: // needed by NLA_PUT_X macros
	return rc;
}

int detour_add_or_del(struct nl_sock *sk, int family, struct in_addr *dip,
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
	if (rc)
		fprintf(stderr, "nl_send_sync failed: %d\n", rc);

nla_put_failure:
	return rc;
}

/* Call DETOUR_C_ECHO, either using CLI provided string or a default. */
int cli_echo(struct nl_sock *sk, int family, int argc, char *argv[])
{
	if (argc == 3) {
		return detour_echo(sk, family, argv[2]);
	} else {
		return detour_echo(sk, family, "hello from userspace!");
	}
}

/* Call DETOUR_C_ADD, using arguments from CLI. */
int cli_add_or_del(struct nl_sock *sk, int family, int argc, char *argv[6],
                   uint8_t cmd)
{
	struct in_addr dip, rip;
	uint16_t dpt, rpt;
	if (argc != 6) {
		fprintf(stderr, "add requires 4 arguments\n");
		fprintf(stderr, "%s %s DIP DPT RIP RPT");
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
	return detour_add_or_del(sk, family, &dip, dpt, &rip, rpt, cmd);
}

/*
 * Uses libnl to send an empty message to the given family or command.
 */
int main(int argc, char *argv[])
{
	int family;
	struct nl_sock *sk;
	int rc = EXIT_SUCCESS;

	if (argc < 2) {
		fprintf(stderr, "expected at least one argument\n");
		return EXIT_FAILURE;
	}

	sk = nl_socket_alloc();
	if (!sk) {
		fprintf(stderr, "nl_socket_alloc returned NULL\n");
		rc = EXIT_FAILURE;
		goto exit;
	}
	rc = genl_connect(sk);
	if (rc != 0) {
		fprintf(stderr, "genl_connect failed: %d\n", rc);
		rc = EXIT_FAILURE;
		goto exit;
	}

	family = genl_ctrl_resolve(sk, DETOUR_FAMILY);
	if (family < 0) {
		fprintf(stderr, "genl_ctrl_resolve failed: %d\n", family);
		rc = EXIT_FAILURE;
		goto exit;
	}

	if (strcmp(argv[1], "echo") == 0) {
		rc = cli_echo(sk, family, argc, argv);
	} else if (strcmp(argv[1], "add") == 0) {
		rc = cli_add_or_del(sk, family, argc, argv, DETOUR_C_ADD);
	} else if (strcmp(argv[1], "del") == 0) {
		rc = cli_add_or_del(sk, family, argc, argv, DETOUR_C_DEL);
	} else {
		fprintf(stderr, "\"%s\" is not a valid command\n", argv[1]);
		rc = EXIT_FAILURE;
	}

exit:
	nl_socket_free(sk);
	return rc;
}
