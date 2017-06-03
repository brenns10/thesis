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
    ax.boxplot(data, labels=labels)
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison: ' + META[base])
    fig.savefig('%s.pdf' % base.replace('.', '-').replace('_', '-'))


def make_all_plots():
    for base in META.keys():
        make_single_plot(base)


def make_time_series_grid(base):
    print(base)
    rows = ['mptcp', 'vanilla']
    cols = ['control', 'nat', 'vpn']
    fig, axarr = plt.subplots(len(rows), len(cols), sharex=True, sharey=True)
    for ridx, row in enumerate(rows):
        for cidx, col in enumerate(cols):
            data = o.get_time_series_arrays('%s.%s.%s.json' % (base, col, row))
            for series in data:
                axarr[ridx][cidx].plot(series[:10])
    axarr[0][0].set_ylabel('MPTCP')
    axarr[1][0].set_ylabel('TCP')
    axarr[1][0].set_xlabel('Control')
    axarr[1][1].set_xlabel('NAT')
    axarr[1][2].set_xlabel('VPN')
    fig.savefig('timegrid-%s.pdf' % base.replace('.', '-').replace('_', '-'))


def make_all_time_series_grid():
    for base in META.keys():
        make_time_series_grid(base)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'time':
        make_all_time_series_grid()
    else:
        make_all_plots()
