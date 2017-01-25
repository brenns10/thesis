CC=gcc
LIBS=libnl-3.0 libnl-genl-3.0
CFLAGS=$(shell pkg-config --cflags $(LIBS))
LDLIBS=$(shell pkg-config --libs $(LIBS))

netlink_client: netlink_client.o
