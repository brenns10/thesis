/**
 * Runs on the client and sends messages to the detour kernel module.
 * build: make client
 * run: ./client CMD [ARGS ...]
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#include <unistd.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <regex.h>

#include <libconfig.h>
#include <netlink/netlink.h>
#include <netlink/attr.h>
#include <netlink/handlers.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>

/**
 * Helper function to perror() and then abort()
 */
void abort_perror(char *msg)
{
	perror(msg);
	abort();
}

/**
 * How many calls should the DETOUR_C_REQ echo handler listen to before quit?
 */
#define MAX_CALLS 5

/**
 * Copied from the kernel; max length of interface name.
 */
#define IFNAMSIZ 16

/**
 * Macro for getting the size of a static array.
 */
#define nelem(arr) (sizeof(arr) / sizeof(arr[0]))

/**
 * A struct for tracking running VPN processes.
 * @next: linked list
 * @openvpn_pid: process ID of the openvpn process
 * @fildes: fildes[1] is stdout of openvpn, read fildes[0] to get output
 * @ifname: interface name associated with it
 */
struct vpn_manager {
	struct vpn_manager *next;
	pid_t openvpn_pid; /* only valid in the parent, obviously */
	int fildes[2];
	char ifname[IFNAMSIZ];
};

/**
 * A struct that holds sockets and addresses for detour entries.
 * @next: linked list
 * @addr: address of detour server
 * @sk: UDP socket connected to detour server
 */
struct detour_manager {
	struct detour_manager *next;
	struct sockaddr_in addr;
	int sk;
};

/**
 * A struct for holding daemon-global data.
 * @vpns: list of vpns
 * @detours: list of detours
 * @sk: netlink socket we listen on
 */
struct daemon_config {
	struct vpn_manager *vpns;
	struct detour_manager *detours;
	struct nl_sock *sk;
};

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
 * Send a request to each UDP socket.
 */
int send_requests(struct daemon_config *dc, struct mproxy_request *req)
{
	struct detour_manager *mgr = dc->detours;
	while (mgr) {
		if (send(mgr->sk, req, sizeof(*req), 0) != sizeof(*req)) {
			perror("failed to send mproxy request");
			return -1;
		}
	}
	return 0;
}

/**
 * Receive a response from each UDP socket and forward it to the kernel. This
 * assumes that we will get a response - it is worth adding a timeout here
 * (TODO).
 */
int recv_responses(struct daemon_config *dc)
{
	struct detour_manager *mgr = dc->detours;
	struct mproxy_request req;
	while (mgr) {
		if (recv(mgr->sk, &req, sizeof(req), 0) != sizeof(req)) {
			perror("failed to recv mproxy response");
			return -1;
		}
		detour_add_or_del(dc->sk, &mgr->addr.sin_addr, req.dpt,
		                  (struct in_addr*)&req.rip, req.rpt,
		                  DETOUR_C_ADD);
	}
	return 0;
}

/**
 * Callback function for DETOUR_C_REQ messages. Parses the message, requests
 * detour(s) via UDP, and then informs the kernel of the new detour(s).
 */
int detour_req_create_cb(struct nl_msg *msg, void *arg)
{
	struct daemon_config *dc = arg;
	struct nlattr *attrs[DETOUR_A_MAX + 1];
	struct nlmsghdr *nlh = nlmsg_hdr(msg);
	struct mproxy_request req;
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

	if (send_requests(dc, &req)) {
		return NL_STOP;
	}

	if (recv_responses(dc)) {
		return NL_STOP;
	}

	return NL_STOP;
}

/**
 * Wait for OpenVPN to initialize itself. We do this by reading lines from its
 * stdout and matching them against regular expressions for particular outputs
 * we need. Once we have seen "Initialization Sequence Completed", we know that
 * we have a happily completed tunnel, and we can return.
 * @param mgr Where we get file descriptors from, and where we'll write ifname
 */
void wait_for_openvpn(struct vpn_manager *mgr)
{
	char buf[512];
	char *if_str = "TUN/TAP device ([[:alnum:]]+) opened";
	char *comp_str = "Initialization Sequence Completed";
	regex_t if_re, comp_re;
	FILE *openvpn;
	regmatch_t matches[2];

	openvpn = fdopen(mgr->fildes[0], "r");
	if (!openvpn)
		abort_perror("fdopen");
	if (regcomp(&if_re, if_str, REG_EXTENDED))
		abort_perror("in regcomp(if_str)");
	if (regcomp(&comp_re, comp_str, REG_EXTENDED))
		abort_perror("in regcomp(comp_str)");

	printf("waiting for device name...\n");
	while (true) {
		if (!fgets(buf, sizeof(buf), openvpn))
			abort_perror("fgets1");
		if (!regexec(&if_re, buf, nelem(matches), matches, 0)) {
			int len = matches[1].rm_eo - matches[1].rm_so;
			len = len < IFNAMSIZ-1 ? len : (IFNAMSIZ-1);
			strncpy(mgr->ifname, buf + matches[1].rm_so, len);
			mgr->ifname[len] = '\0';
			break;
		}
	}

	printf("waiting for initialization sequence...\n");
	while (true) {
		if (!fgets(buf, sizeof(buf), openvpn))
			abort_perror("fgets2");
		if (!regexec(&comp_re, buf, nelem(matches), matches, 0)) {
			break;
		}
	}
}

/**
 * Fork and launch OpenVPN in client mode. Returns in the parent, not the child.
 * @param addr Address of the remote server
 * @returns A pointer to the filled out struct vpn_manager
 */
struct vpn_manager *detour_launch_openvpn(const char *addr)
{
	pid_t pid;
	struct vpn_manager *mgr;
	const char *openvpn_args[] = {
		"openvpn",
		"--remote", NULL, /* only add/modify args below this one! */
		"--client",
		"--dev", "tun",
		"--ca", "ca.crt",
		"--cert", "client1.crt",
		"--key", "client1.key",
		"--topology", "p2p",
		"--pull",
		"--nobind",
		NULL, /* this must be the last one */
	};
	openvpn_args[2] = addr;

	mgr = malloc(sizeof(struct vpn_manager));
	mgr->next = NULL;
	if (pipe(mgr->fildes) == -1) {
		perror("error in pipe()");
		free(mgr);
		return NULL;
	}

	pid = fork();
	if (pid == -1) {
		/* error */
		perror("error forking");
		free(mgr);
		return NULL;
	} else if (pid == 0) {
		/* child */
		if (dup2(mgr->fildes[1], STDOUT_FILENO) == -1) {
			perror("dup2 failed in child");
			exit(EXIT_FAILURE);
		}
		if (execvp("openvpn", /*shutup*/(char * const*)openvpn_args) == -1) {
			perror("execvp failed in child");
			exit(EXIT_FAILURE);
		}
		/* because i'm paranoid */
		exit(EXIT_SUCCESS);
	} else {
		/* parent */
		mgr->openvpn_pid = pid;
		wait_for_openvpn(mgr);
		return mgr;
	}
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
 * Return a "detour manager" for a given IP address, or NULL on error.
 * TODO: allow hostnames
 */
struct detour_manager *make_detour_manager(const char *ipaddr)
{
	struct detour_manager *mgr = malloc(sizeof(struct detour_manager));
	mgr->addr.sin_family = AF_INET;
	if (!inet_aton(ipaddr, &mgr->addr.sin_addr)) {
		fprintf(stderr, "invalid detour ip address\n");
		goto destroy;
	}
	mgr->addr.sin_port = MPROXY_DEFAULT_PORT;
	mgr->sk = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	if (mgr->sk == -1) {
		perror("socket");
		goto destroy;
	}
	if (connect(mgr->sk, (struct sockaddr*)&mgr->addr,
	            sizeof(struct sockaddr)) == -1) {
		perror("connect");
		goto destroy;
	}
	return mgr;
destroy:
	free(mgr);
	return NULL;
}

/**
 * Free resources held by a detour manager list (socket and memory)
 */
void destroy_detour_list(struct detour_manager *mgr)
{
	struct detour_manager *next;
	while (mgr) {
		next = mgr->next;
		close(mgr->sk);
		free(mgr);
		mgr = next;
	}
}

/**
 * Free resources held by a detour manager list (kills openvpn, closes its
 * stdout, and frees memory associated with manager).
 */
void destroy_vpn_list(struct vpn_manager *mgr)
{
	struct vpn_manager *next;
	while (mgr) {
		next = mgr->next;
		kill(mgr->openvpn_pid, SIGTERM);
		close(mgr->fildes[0]);
		close(mgr->fildes[1]);
		free(mgr);
		mgr = next;
	}
}

/**
 * Free resources held by a daemon_config (detour and vpn list, as well as
 * memory)
 */
void destroy_daemon_config(struct daemon_config *dc)
{
	destroy_detour_list(dc->detours);
	destroy_vpn_list(dc->vpns);
	free(dc);
}

/**
 * Initializes the daemon from a configuration file.
 * - Parse libconfig file at filename, and create a data structure with info
 * - Create sockets for each detour listed
 * - Create OpenVPN processes for each VPN listed
 * Returns NULL on error. Returned pointer should be destroyed with
 * destroy_daemon_config()
 */
struct daemon_config *parse_config(char *filename)
{
	struct daemon_config *dc = malloc(sizeof(struct daemon_config));
	struct detour_manager *mgr = NULL;
	struct vpn_manager *vmgr = NULL;
	const char *ip;
	config_t conf;
	config_setting_t *setting;

	int i, len;
	config_init(&conf);
	if (config_read_file(&conf, filename) != CONFIG_TRUE) {
		fprintf(stderr, "%s:%d: error: %s\n", config_error_file(&conf),
		        config_error_line(&conf), config_error_text(&conf));
		goto destroy;
	}

	/* Get "detour" items from config. */
	setting = config_lookup(&conf, "client.detours");
	if (!setting || !config_setting_is_aggregate(setting)) {
		fprintf(stderr, "setting client.detours not found\n");
		goto destroy;
	}
	len = config_setting_length(setting);
	dc->detours = NULL;
	for (i = 0; i < len; i++) {
		ip = config_setting_get_string_elem(setting, i);
		if (!ip) {
			fprintf(stderr, "detours must be strings\n");
			goto destroy_detours;
		}
		mgr = make_detour_manager(ip);
		if (!mgr)
			goto destroy_detours;
		mgr->next = dc->detours;
		dc->detours = mgr;
	}

	/* Get "vpn" items from config */
	setting = config_lookup(&conf, "client.vpns");
	if (!setting || !config_setting_is_aggregate(setting)) {
		fprintf(stderr, "setting client.vpns not found\n");
		goto destroy_detours;
	}
	len = config_setting_length(setting);
	dc->vpns = NULL;
	for (i = 0; i < len; i++) {
		ip = config_setting_get_string_elem(setting, i);
		if (!ip) {
			fprintf(stderr, "vpns must be strings\n");
			goto destroy_vpns;
		}
		vmgr = detour_launch_openvpn(ip);
		if (!vmgr)
			goto destroy_vpns;
		vmgr->next = dc->vpns;
		dc->vpns = vmgr;
	}

	return dc;
destroy_vpns:
	destroy_vpn_list(dc->vpns);
destroy_detours:
	destroy_detour_list(dc->detours);
destroy:
	config_destroy(&conf);
	return NULL;
}

/**
 * Daemon-mode for cli. This is the "main point" of this client: wait for detour
 * requests from the kernel, send them to our detour server, and inform the
 * kernel of the newly available detours.
 */
int cli_daemon(struct nl_sock *sk, int argc, char *argv[])
{
	char *filename = "daemon.conf";
	struct daemon_config *dc;
	int rc;
	if (argc >= 3) {
		/* get config file override */
		filename = argv[2];
	}
	dc = parse_config(filename);
	if (!dc) {
		return -1;
	}
	dc->sk = sk;
	/* Setup netlink callback and group membership for receiving */
	rc = nl_socket_add_memberships(sk, group, NFNLGRP_NONE);
	if (rc < 0) {
		nl_perror(rc, "nl_socket_add_memberships");
		goto destroy_dc;
	}
	rc = nl_socket_modify_cb(sk, NL_CB_MSG_IN, NL_CB_CUSTOM,
	                         detour_req_create_cb, dc);
	if (rc < 0) {
		nl_perror(rc, "nl_cb_set");
		goto destroy_dc;
	}
	nl_socket_disable_seq_check(sk);
	/* now we loop receiving netlink messages */
	do {
		rc = nl_recvmsgs_default(sk);
	} while (rc >= 0);
	if (rc < 0) {
		nl_perror(rc, "nl_recvmsgs");
	}
destroy_dc:
	destroy_daemon_config(dc);
	return rc;
}

/** Run two vpn connections and report their ifnames, for diagnostics. */
int cli_vpn(struct nl_sock *sk, int argc, char *argv[])
{
	(void)sk;
	if (argc != 3) {
		fprintf(stderr, "need an address");
		return -1;
	}
	struct vpn_manager *vpn1 = detour_launch_openvpn(argv[2]);
	struct vpn_manager *vpn2 = detour_launch_openvpn(argv[2]);
	printf("vpn1: %s, vpn2: %s\n", vpn1->ifname, vpn2->ifname);
	return 0;
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
	} else if (strcmp(argv[1], "vpn") == 0) {
		rc = cli_vpn(sk, argc, argv);
	} else {
		fprintf(stderr, "\"%s\" is not a valid command\n", argv[1]);
		rc = EXIT_FAILURE;
	}

exit:
	nl_socket_free(sk);
	return rc;
}
