Sockets
=======

The biggest barrier to understanding the MPTCP implementation is understanding
what data structures are and how they're used. The word socket is overloaded in
the kernel and there are many sockets involved in a typical MPTCP session, so
it's important for me to read, understand, and document how they are used.

TCP Socket
----------

The `struct tcp_sock` object is defined in `include/linux/tcp.h`, and one
instance seems to exist for each subflow, and more generally, for each regular
TCP connection. There are some MPTCP-related fields within this structure, most
importantly `mptcp`, which is a pointer to the `struct mptcp_tcp_sock`.

The TCP socket contains a pointer to the `mptcp_cb`, which is also something
that will be discussed shortly.

MPTCP TCP Socket
----------------

The `struct mptcp_tcp_sock` seems to exist for every MPTCP subflow. It appears
to contain some of the more MPTCP-specific information. It is in a linked list
of every subflow in the connection. It includes information about the data
sequence mapping, and it also contains some scheduler info.

It is allocated separately from the TCP socket, and it is created in
`mptcp_add_socket`.

Control Buffer
--------------

We need to have shared state for a MPTCP flow as a whole. The above socket types
are subflow-specific. The main data structure related to the connection as a
whole is the `struct mptcp_cb`, aka the MPTCP control buffer. The traditional
variable name is `mpcb`. The mpcb contains several things.

- `connection_list` points to a subflow's `tcp_sock`, which is linked to the
  rest through the `mptcp_tcp_sock`.
- `meta_sk` points to the meta socket (more on that in a moment)
- `master_sk` points to the master socket
- `mptcp_pm` is a buffer that path managers use for private data

Each subflow has a pointer to the mpcb in the `tcp_sock`.

Meta and Master Sockets
-----------------------

The control buffer holds plenty of information about the connection as a whole,
but there are a couple additional things. In particular, it makes sense that the
MPTCP connection itself should have a socket, and it does. The meta socket is
another `tcp_sock` that represents the connection as a whole, and it implements
the data-level operations while the subflow sockets implement the subflow level
operations. The meta socket is not present in the list of subflow sockets.

The master socket is the first subflow socket. It is contained within the
subflow list.

There are competing sources on whether the application is linked to the master
or the meta socket. A [draft][barre] of implementation notes from 2011 seems to
suggest that the master socket is the one linked to the application. However, a
more recent [paper][paper] on the architecture makes no mention of master
sockets and instead implies that the meta socket is the one linked to the
application.

If I had to guess, the initial implementation kept the application linked to the
master socket, but that has changed (probably as a way to simplify things).
However, I don't know, and this is just a guess.

[barre]: https://tools.ietf.org/html/draft-barre-mptcp-impl-00
[paper]: https://irtf.org/anrw/2016/anrw16-final16.pdf
