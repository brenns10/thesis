/**
 * nsdo: run a command within a namespace
 */
#define _GNU_SOURCE

#include <sys/stat.h>
#include <fcntl.h>
#include <sched.h>
#include <stdlib.h>
#include <stdio.h>

int main(int argc, char *argv[])
{
	if (argc < 3) {
		fprintf(stderr, "usage: %s NSFILE cmd [args...]", argv[0]);
		return EXIT_FAILURE;
	}

	int fd = open(argv[1], O_RDONLY);
	if (fd < 0) {
		perror("open");
		return EXIT_FAILURE;
	}

	if (setns(fd, 0) == -1) {
		perror("setns");
		return EXIT_FAILURE;
	}

	execvp(argv[2], &argv[2]);
	// If exec*() returns, it's an error
	perror("execvp");
	return EXIT_FAILURE;
}
