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

# order preserved
SCEN = {
    'server.ctrl.mptcp': '1 Subflow',
    'server.nat.mptcp': 'NAT',
    'server.vpn.mptcp': 'VPN',
    'server.ctrl.vanilla': 'TCP',
    'server.nat.vanilla': 'TCP (NAT)',
    'server.vpn.vanilla': 'TCP (VPN)',
}


def make_throughput_plot():
    data = []
    labels = []
    for s, label in SCEN.items():
        data.append(o.get_numpy_array('%s.json' % s) / 1000000)
        labels.append(label)

    fig, ax = plt.subplots()
    print(list(map(len, data)))
    ax.boxplot(data, 0, '', labels=labels)
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title('Throughput Comparison: AWS')
    fig.savefig('aws.pdf')


def make_time_series_grid():
    rows = ['mptcp', 'vanilla']
    cols = ['ctrl', 'nat', 'vpn']
    fig, axarr = plt.subplots(len(rows), len(cols), sharex=True, sharey=True)
    for ridx, row in enumerate(rows):
        for cidx, col in enumerate(cols):
            data = o.get_time_series_arrays('server.%s.%s.json' % (col, row))
            for series in data:
                axarr[ridx][cidx].plot(series[:10])
    axarr[0][0].set_ylabel('MPTCP')
    axarr[1][0].set_ylabel('TCP')
    axarr[1][0].set_xlabel('Control')
    axarr[1][1].set_xlabel('NAT')
    axarr[1][2].set_xlabel('VPN')
    fig.savefig('timegrid-aws.pdf')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'time':
        make_time_series_grid()
    else:
        make_throughput_plot()
