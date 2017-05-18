#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Produce plots.
"""

from os.path import dirname, abspath
import sys
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import output as o

import matplotlib.pyplot as plt

# order preserved (thanks python 3.6...?)
META = {
    'easy': 'Core-limited',
    'lossy': 'Core-limited with Loss',
    'delayed': 'Core-limited with High Latency',
    'sym': 'Symmetric',
    'sym_lossy': 'Symmetric with Loss',
    'sym_delayed': 'Symmetric with High Latency',
}

# order preserved
SCEN = {
    'control.mptcp': '1 Subflow',
    'nat.mptcp': 'NAT',
    'vpn.mptcp': 'VPN',
    'control.vanilla': 'TCP',
    'nat.vanilla': 'TCP (NAT)',
    'vpn.vanilla': 'TCP (VPN)',
}


def make_single_plot(base):
    print(base)
    data = []
    labels = []
    for s, label in SCEN.items():
        data.append(o.get_numpy_array('%s.%s.json' % (base, s)) / 1000000)
        labels.append(label)

    fig, ax = plt.subplots()
    print(list(map(len, data)))
    ax.boxplot(data, 0, '', labels=labels)
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison: ' + META[base])
    fig.savefig('%s.pdf' % base)


def make_all_plots():
    for base in META.keys():
        make_single_plot(base)


if __name__ == '__main__':
    make_all_plots()
