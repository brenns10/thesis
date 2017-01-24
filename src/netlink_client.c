/*
 * Runs on the client and sends messages to the detour kernel module.
 * build: gcc netlink_client.c -o netlink_client $(pkg-config --cflags --libs libnl-3.0)
 * run: ./netlink_client COMMAND_NUM
 */

#include <stdio.h>
#include <stdlib.h>
#include <netlink/netlink.h>
#include <netlink/genl/genl.h>
#include <netlink/genl/ctrl.h>

#define DETOUR_FAMILY "DETOUR"
#define DETOUR_VERSION 1

/*
 * print usage information and exit
 */
void usage(char *name)
{
	fprintf(stderr, "usage: %s COMMAND_NUM\n", name);
	fprintf(stderr, "Send a message to the MPTCP detour kernel module.\n");
	exit(EXIT_FAILURE);
}

/*
 * Uses libnl to send an empty message to the given family or command.
 */
int main(int argc, char *argv[])
{
	int family;
	uint8_t cmd;
	struct nl_sock *sk;
	int rc;

	if (argc < 2)
		usage(argv[0]);

	cmd = (uint8_t)atoi(argv[1]);
	if (!cmd)
		fprintf(stderr, "cmd was 0, may be error...\n");

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

	rc = genl_send_simple(sk, family, cmd, DETOUR_VERSION, 0);
	if (!rc)
		fprintf(stderr, "genl_send_simple failed: %d\n", rc);

exit:
	nl_socket_free(sk);
	return rc;
}
