#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse JSON output of experiments."""

import itertools
import json

import numpy as np
import matplotlib.pyplot as plt


def json_parse(filename):
    """Parse a file that contains a bunch of JSON objects.

    This assumes that each object starts and ends
    """
    with open(filename) as f:
        string = ''
        for line in f:
            string += line
            try:
                yield json.loads(string)
                string = ''
            except:
                pass


def objects_to_bps(obj_list):
    """Converts a sequence of JSON objects to the bits per second."""
    for obj in obj_list:
        bps = obj.get('end', {}).get('sum_received', {}).get('bits_per_second')
        if bps:
            yield bps


def objects_to_utilization(obj_list):
    """Converts a sequence of JSON objects to their CPU utulization average."""
    for obj in obj_list:
        # remote_total tends to be a percent or two higher, report it to be
        # conservative
        u = obj.get('end', {}).get('cpu_utilization_percent', {}).get('remote_total')
        if u:
            yield u


def show_max_utilization(filenames):
    """Report the max CPU utilization of all the JSON files."""
    all_utilization = map(objects_to_utilization, map(json_parse, filenames))
    chained = itertools.chain.from_iterable(all_utilization)
    print(max(chained))


def get_numpy_array(filename):
    return np.array(list(objects_to_bps(json_parse(filename))))


def time_series(obj):
    return np.array([o['sum']['bits_per_second'] for o in obj['intervals']]) / 1000000


def get_time_series_arrays(filename):
    return list(map(time_series, json_parse(filename)))


def plot_comparison(name):
    mptcp_ctrl = get_numpy_array('%s.control.mptcp.json' % name) / 1000000
    mptcp_nat = get_numpy_array('%s.nat.mptcp.json' % name) / 1000000
    mptcp_vpn = get_numpy_array('%s.vpn.mptcp.json' % name) / 1000000
    vanilla_ctrl = get_numpy_array('%s.control.vanilla.json' % name) / 1000000
    vanilla_nat = get_numpy_array('%s.nat.vanilla.json' % name) / 1000000
    vanilla_vpn = get_numpy_array('%s.vpn.vanilla.json' % name) / 1000000
    fig, ax = plt.subplots()
    data = [mptcp_ctrl, mptcp_nat, mptcp_vpn, vanilla_ctrl, vanilla_nat,
            vanilla_vpn]
    labels = ['1 Sub flow', 'NAT', 'VPN', 'TCP', 'TCP(NAT)', 'TCP(VPN)']
    print(list(map(len, data)))
    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison (%s)' % name)


if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'cpu':
        print('Computing max CPU utilization.')
        filenames = sys.argv[2:]
        show_max_utilization(filenames)
