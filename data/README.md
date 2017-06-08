Data
====

This directory is heavily cluttered, but I don't really want to clean it up for
fear of data loss. Instead, I'll just guide the reader to what is relevant and
not.

What's not relevant:
- Ipython notebooks (they're outdated)
- JSON files in `data/` -- relevant JSON files are stored within subdirectories
- Many of the subdirectories contain old data which had bugs or defects in it

What is relevant:
- Python scripts in this directory are used by scripts within subdirectories for
  some plumbing stuff
- The `aws4` directory contains AWS data which is used in the paper
- The `2017-05-21-cpu-limit` directory contains the main mininet experiment data
- The `param_validation` directory contains data from parameter validation
  experiments which look at different loss/latency rates
- The `cap` directory contains packet captures for some of the experiment
  configurations. It also contains some really cool "xplot" graphs and tcptrace
  output, which is used in the paper as well. Check its README for more details.
