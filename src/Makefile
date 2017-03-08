CC=gcc
LIBS=libnl-3.0 libnl-genl-3.0 libconfig
CFLAGS=$(shell pkg-config --cflags $(LIBS))
LDLIBS=$(shell pkg-config --libs $(LIBS))

client: client.o
