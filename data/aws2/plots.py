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
    'server.ctrl': '1 Subflow',
    'server.nat': 'NAT',
    'server.vpn': 'VPN',
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
    fig, axarr = plt.subplots(1, len(SCEN), sharex=True, sharey=True)
    for cidx, col in enumerate(SCEN.keys()):
        data = o.get_time_series_arrays('%s.json' % col)
        for series in data:
            axarr[cidx].plot(series[:10])
    axarr[0].set_ylabel('Throughput (Mbps')
    axarr[0].set_xlabel('1 Subflow')
    axarr[1].set_xlabel('NAT')
    axarr[2].set_xlabel('VPN')
    fig.savefig('timegrid.aws.pdf')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'time':
        make_time_series_grid()
    else:
        make_throughput_plot()
