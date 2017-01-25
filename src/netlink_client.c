/*
 * Runs on the client and sends messages to the detour kernel module.
 * build: make netlink_client
 * run: ./netlink_client COMMAND_NUM
 */

#include <stdio.h>
#include <stdlib.h>
#include <netlink/netlink.h>
#include <netlink/attr.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>

/*
 * The following are shamelessly taken from the kernel code.
 */
#define DETOUR_FAMILY "DETOUR"
#define DETOUR_C_ECHO 1
#define DETOUR_VERSION 1
#define DETOUR_A_MSG 1

/*
 * Uses libnl to send an empty message to the given family or command.
 */
int main(int argc, char *argv[])
{
	int family;
	struct nl_sock *sk;
	int rc;

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
	} else {
		printf("resolved family %s to %d\n", DETOUR_FAMILY, family);
	}

	struct nl_msg *msg = nlmsg_alloc();
	if (!msg) {
		fprintf(stderr, "nlmsg_alloc() returned NULL\n");
		rc = EXIT_FAILURE;
		goto exit;
	}
	//               msg, port,         seq,      family, hdrlen, flags, cmd
	if (!genlmsg_put(msg, NL_AUTO_PORT, NL_AUTO_SEQ, family, 0, 0,
	                 DETOUR_C_ECHO, DETOUR_VERSION)) {
		fprintf(stderr, "genlmsg_put() failed\n");
		rc = EXIT_FAILURE;
		goto exit;
	}
	NLA_PUT_STRING(msg, DETOUR_A_MSG, "hello, kernel");

	rc = nl_send_auto_complete(sk, msg);
	if (!rc)
		fprintf(stderr, "nl_send_auto_complete failed: %d\n", rc);

nla_put_failure: // needed by NLA_PUT_X macros
exit:
	nl_socket_free(sk);
	return rc;
}
