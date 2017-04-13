Mininet
=======

There's a lot to be said for Mininet. Having gone through the FAQs, API
documentation, walkthroughs, and a good portion of the code, I feel like I'm
still missing several bits of information. (what is a controller? why do we need
openvswitch when the kernel has its own switching capabilites? why do they care
so much about the switches? I could go on...)

However I'm just going to stick to the hard-earned bits of information that I
had to fight to learn.

Topologies
----------

The whole topology concept in Mininet is pretty damn rigid. The whole project
seems to assume that you care waaay to much about switches, and not nearly
enough about the network layer and above. So, while it is quite simple to create
a topology with hosts connected by switches, hosts connected by routers cannot
be created simply by a topology.

Rather, you need to build a whole replacement for the `mn` command, along with a
topology. After you start the network, you need to assign IP addresses (because
topologies can't assign more than one IP to a host!), create routing tables, and
enable forwarding on your routers. Several samples are in my `src/` directory.

OpenVSwitch
-----------

The mininet project is full of stupid references to OVS, and all of these dumb
SDN tools. As far as I can tell, if all you want is to connect hosts to each
other without switches, you can get away without having any of that crap
installed. My noswitch and detour topologies illustrate that.

Namespaces
----------

These turned out to be really important (sorry past Stephen). I wrote a whole
[article][] about how to do Wireshark monitoring within these namespaces.

[article]: https://brennan.io/2017/04/12/wireshark-tricks/
