CC=gcc
LIBS=libnl-3.0 libnl-genl-3.0 libconfig
CFLAGS=$(shell pkg-config --cflags $(LIBS)) --std=gnu11
LDLIBS=$(shell pkg-config --libs $(LIBS))

.PHONY: all clean
all: client nsdo
clean:
	rm -f client client.o nsdo nsdo.o

client: client.o
nsdo: nsdo.o
