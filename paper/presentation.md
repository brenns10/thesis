Presentation
============

Timeline
--------

According to Misha, the talk portion of the defense runs about 50 minutes.
Here's a rough breakdown of how much time I want to spend on each section:

- Introduction (7 minutes)
- Background (8 minutes)
- Related work (5 minutes)
- Mechanism (18 minutes)
- Evaluation (7 minutes)
- Conclusion (5 minutes)

Rehearsal Comments
------------------

- [x] Number slides!
- [x] In overview - no point about the "idea"
- [x] Shortest path - in terms of AS hops
- [x] See if you can squeeze actual paper refs
- [x] Cut these "We are going to move right along" transitions. Rather, "before
  explaining my solution to ... let us briefly survey the background information
  on MPTCP and related work". E.g., your transition to Rel Work was fine.
- [x] Mention that MPTCP API to apps is unchanged.
- [x] Check how much apps are affected by mTCP
- [x] Avoid statements like "A last piece of rel work" - you can never claim you
  found the last re. work.
- [x] Perhaps title the slide with with triangular communication "Idea
  Overview"?
- [ ] Have a diagram for interaction between components on the client?
  - In particular, this comment means to show graphically the steps that happen
    for a run of the mechanism (arrow showing request moving through, etc)
- [x] Evaluation of the overhead?
- [x] What is the workload in your experiments?
- [x] Detour collective - sharing economy?
- [x] Related work - mention HTTP range requests and requesting embedded objects
  in parallel from different server replicas
- [x] (**Big One**) Use packet trace to see what fraction of data went along
  each subflow.
