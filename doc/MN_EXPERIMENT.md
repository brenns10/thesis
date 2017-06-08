Mininet Experiment
==================

To run a Mininet experiment, you'll need the following:

- A `vm.tar` (see `VM_TAR.md`)
- A Mininet VM with the `vm.tar` installed on it (see `VM.md`)

Log into the machine (I used ssh but the VM console works just as well) as
the mininet user (password mininet). Enter the `src` directory and use the
`mn_experiment.sh` script. This calls `experiment.py` once for every
configuration.

You may notice that `experiment.py` is actually capable of taking multiple
experiment configurations and running all of them. Unfortunately, when you do
this Mininet doesn't get the chance to clean up, and you get really weird
results. This is why I have a driver shell script to run the experiments.

When you run the experiments using the custom MPTCP kernel, the scripts will
output data files which include `mptcp` in the filename. When you run them on a
kernel which doesn't support MPTCP, you'll see `vanilla` in the filename. You'll
want both sets of data. The data files are `json` files produced within the
`src` directory.

For post-processing, you'll want to copy the json files out of the VM. I always
put them directly into the `data` directory. You can examine the scripts within
`data` and its subdirectories to see how I plotted things.
