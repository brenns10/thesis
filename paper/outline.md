# Thesis Outline

The no-bullshit high-level outline and overview of the paper.

## Introduction

Before we go into the subsections of the Introduction, the header paragraph
describes what this is, and why. Should be a paragraph or two. Don't go all user
story or anything. Don't want to make unsubstantiated claims.

### Inefficiencies in Internet Routing

Describe the eagle's eye view of how the internet works (a few sentences).
Describe how routing occurs, and the major protocols working in the background.

Then, basically cite detour a bunch to say that the Internet routed path is not
always best.

Talk about overlay routing systems, in general.

### Underutilization of Access Links

Cite Allman to say that high-bandwidth access links aren't heavily utilized. If
access links are mostly free, and there are better paths to use, why not use
them? Additionally, why not combine them until your access links can't handle
it?

Give the concept. Use multiple paths to your destination in your flow, in order
to improve throughput.

### Contributions

Then, describe what exactly it is that this thesis does.
1. A mechanism for using MPTCP and routing using detours.
2. Evaluation that demonstrates that the approach can aggregate bandwidth.

## Background and Related Work

### MPTCP
- mention SCTP

Here I can give a full working knowledge of the MPTCP protocol. As I've laid out
in the comments of my paper, this should include:

- Subflows: what they are and how they work
- How the initial subflow is created
- How subsequent subflows are created and authenticated
- Data sequencing and how data sequences are mapped onto subflow sequences
- path management and data scheduling
- ? how the linux kernel implementation is structured

### Overlay Routing

Discuss the many studies which have been done. Make sure to differentiate.
- Detour
- RON
- oTCP?

Perhaps a subsubsection saying what we do that's different from the others.

### Netfilter, OpenVPN

I have sections for Netfilter and OpenVPN. These are already getting a fair
amount of discussion in the implementation section. I may not need to add
introductions here.

## Implementation

Here I give the overview of what all the pieces are and how they fit together.

### Detour Daemon

Here I discuss both methods of tunneling. I should probably also touch on the
major trade-offs between the two methods - 1 RTT for NAT setup, vs header
overhead for OpenVPN. I should also mention that there are 0RTT methods, and
refer the reader to the Related Work section where I will discuss the plain-mode
MPTCP proxy draft.

#### OpenVPN

Here I've also discussed a fair amount of OpenVPN background. Some important
topics to cover:

- MSS can be a tricky issue
- Authentication, encryption

#### NAT

Here I've discussed a fair amount of Netfilter background.

### Path Manager

Here I discuss the kernel component.

### Client Daemon

Here I discuss the userspace client component. It seems that I have lumped in a
lot of background discussion on Netlink here.

## Evaluation

Here I should lay out my framework for evaluating. In particular, that the goal
of the project is not to identify route selection techniques, but rather to
create a new mechanism which can dynamically add and remove routes, and also
aggregate the throughput of available detour routes.

### Simulation

The purpose here is to show that the mechanism works in a controlled
environment. Furthermore, this experiment also exists to demonstrate that given
the right conditions, the mechanism will effectively aggregate path bandwidth.

- Describe the Mininet tool. May be its own little section.
- Describe the network topology I used, as well as the different network
  conditions I have simulated.
- Also make sure to drop in that I used Cubic congestion control.

### AWS Experiment

The purpose of this experiment is not necessarily to show path aggregation, but
simply to demonstrate that the mechanism can used across the Internet today,
without significant deployment effort. The mechanism can scale to larger
throughputs and real Internet paths rather than ones simulated in a single
kernel.

## Discussion and Future Work

Probably I will have pointed out major takeaways from the experiments already.
If not, now is the place to discuss it. It is also a good place to take a stand
on the pros and cons of the two tunneling methods. It may be good to get some
statistical significance on my experiments by upping the number of trials. The
data points to the direction that the overhead of OpenVPN is noticeable compared
to NAT, where the setup cost doesn't seem to be noticeable. However, the
correctness of the NAT solution is a bit flaky - address indices especially are
fudged.

I can then discuss the possibility of future work. There are several components
that can be improved on:

- Better dynamic route selection. Currently we can dynamically add and delete
  routes, but the client daemon does not do anything particularly exciting.
- A central (or decentralized) service where users join the overlay network,
  agreeing to provide detouring services in exchange for using others' detouring
  services.
  
## Conclusion

Not sure what will go here beyond a rehash of what happened.
