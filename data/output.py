#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse JSON output of experiments."""

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


def get_numpy_array(filename):
    return np.array(list(objects_to_bps(json_parse(filename))))


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
    labels = ['1 Subflow', 'NAT', 'VPN', 'TCP', 'TCP(NAT)', 'TCP(VPN)']
    print(list(map(len, data)))
    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison (%s)' % name)
