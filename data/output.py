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
    ctrl = get_numpy_array('%s.control.json' % name) / 1000000
    nat = get_numpy_array('%s.nat.json' % name) / 1000000
    vpn = get_numpy_array('%s.vpn.json' % name) / 1000000
    print(len(ctrl), len(nat), len(vpn))
    fig, ax = plt.subplots()
    ax.boxplot([ctrl, nat, vpn], labels=['Control', 'NAT', 'VPN'])
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison (%s)' % name)
