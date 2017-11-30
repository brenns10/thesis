Data
====

This directory is heavily cluttered, but I don't really want to clean it up for
fear of data loss. Instead, I'll just guide the reader to what is relevant and
not.

What's not relevant:
- The IPython notebook

What's not very relevant:
- Old results for Mininet experiments (the ones before 2017-05-21)
- Old results for AWS experiments (aws-aws3)
- As a rule, old results contain bugs!

What's very relevant:
- output.py contains utilities for creating plots! (requires matplotlib)
- 2017-05-21-cpu-limit is the latest Mininet experiment data
- aws4 is the latest AWS experiment data
- cap contains captures from Mininet experiments (src/make_captures.sh)

Mininet Results
---------------

The directories with dates on them are Mininet results. They each contain a
plot.py script, which can be used to generate PDF graphs from the JSON outputs.

If you generate new JSON results, create a new subdirectory. Copy the most
recent plot.py in there. Run the script and cross your fingers!

AWS Results
-----------

The directories named `aws` have AWS results (shocker). Plot generation is much
the same as Mininet experiments.

Captures
--------

Packet captures were generated with `src/make_captures.sh` in the Mininet VM.
You can view existing plots (.xpl files) with `xplot`. Unfortunately, I used
a non-public tool for generating the xpl files, so you cannot create your own
plots, but most of the rest is ok. See my `capplot.sh` script for details.
