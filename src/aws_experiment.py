#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Detour Experiment

This script creates several EC2 instances in different datacenters. It does the
necessary initialization to each of the hosts, waits for their initialization
to complete, and then runs some experiments on them.

Prerequisites:
1. You must have an SSH key pair. You must import it into EC2 on *each* region
   the experiment will run. While this could be automated, I would prefer not
   to bother with APIs that center around one-off configuration.
2. The default security group of the default VPC ought to be configured to
   to allow ingress on any port. By default it allows ingress from other
   members of the security group, egress to anywhere. If nothing else, add SSH
   ingress. It's just much more convenient. And I don't want to do it
   programmatically.

"""
import os
import re
import sys
from io import BytesIO
from os.path import abspath
from os.path import dirname
from os.path import join

import boto3
import paramiko


TRIALS = 100

NAT_CFG = '''
client: {
  detours = ["%s"];
  vpns = [];
  daemonize = false;
  logfile = "daemon-nat.log";
  loglevel = "DEFAULT";
}
'''

VPN_CFG = '''
client: {
  detours = [];
  vpns = ["%s"];
  daemonize = false;
  logfile = "daemon-vpn.log";
  loglevel = "DEFAULT";
}
'''

# Key Pair Name. Hopefully you named it the same thing in every region.
KEYPAIR = os.getenv('KEYPAIR') or 'stephen@greed'
KEYFILE = os.getenv('KEYFILE') or '/home/stephen/.ssh/id_rsa'

# The filename of the AWS setup script.
SETUP_SCRIPT = join(dirname(abspath(__file__)), '../etc/aws_exp_setup.sh')
SETUP_SCRIPT_VANILLA = join(dirname(abspath(__file__)), '../etc/aws_exp_setup_vanilla.sh')

# These tags are applied to everything we create, so it's easier to clean up
# via the Console if things go wrong.
TAGS = [
    {'Key': 'Project', 'Value': 'Thesis'},
]
TAG_FILTER = [
    {'Name': 'tag:Project', 'Values': ['Thesis']}
]


# These become arguments to boto3.resource('ec2')
RESOURCE_PARAMS = {}
RESOURCE_PARAMS_EACH = {
    'client': {
        'region_name': 'us-west-1', # N. California
    },
    'detour': {
        'region_name': 'us-east-2', # Ohio
    },
    'server': {
        'region_name': 'us-east-1', # N. Virginia
    },
}

# These become arguments to ec2.create_instances()
CREATE_INSTANCES_PARAMS = {
    'MinCount': 1,
    'MaxCount': 1,
    'UserData': open(SETUP_SCRIPT).read(),
    'InstanceType': 'm4.large',
    'TagSpecifications': [
        {
            'ResourceType': 'instance',
            'Tags': TAGS,
        },
    ],
    'KeyName': KEYPAIR,
}
CREATE_INSTANCES_PARAMS_EACH = {
    'client': {
        'ImageId': 'ami-30476250',
    },
    'detour': {
        'ImageId': 'ami-33ab8f56',
    },
    'server': {
        'ImageId': 'ami-e4139df2',
    },
}


def merge(d1, d2):
    """Merge two structures of nested dicts and lists.

    d1 and d2 are not modified.

    The semantics are straightforward. d1 is "updated" with contents of d2.
    For each key in d2, it will either be recursively merged (if a dict),
    concatenated (if a list), or replace (otherwise) the corresponding value in
    d1.
    """
    d1 = d1.copy()
    for k, v in d2.items():
        if isinstance(v, dict):
            d1[k] = merge(d1.get(k, {}), v)
        elif isinstance(v, list):
            d1[k] = d1.get(k, []) + list(v)
        else:
            d1[k] = v
    return d1


def resource_params(k):
    v = merge(RESOURCE_PARAMS, RESOURCE_PARAMS_EACH[k])
    return v


def create_instances_params(k):
    v = merge(CREATE_INSTANCES_PARAMS, CREATE_INSTANCES_PARAMS_EACH[k])
    return v


def create_instances(vanilla=False):
    instances = {}
    for k in RESOURCE_PARAMS_EACH.keys():
        print('Creating instance %s...' % k)
        resource = boto3.resource('ec2', **resource_params(k))
        params = create_instances_params(k)
        if vanilla:
            params['UserData'] = open(SETUP_SCRIPT_VANILLA).read()
        instance = resource.create_instances(**params)
        assert len(instance) == 1
        instances[k] = instance[0]
    return instances


def first_time_wait(instances):
    for k, inst in instances.items():
        print('Waiting until instance %s is running...' % k)
        inst.wait_until_running()

    # Now they are all running their initialization scripts. They will shut
    # down on completion, so that when they come up again, they are in their
    # new kernels. So, we now wait until they are stopped!

    for k, inst in instances.items():
        print('Waiting until instance %s is stopped...' % k)
        inst.wait_until_stopped()

    # Now that they have all stopped, we can boot them again.

    for k, inst in instances.items():
        print('Starting instance %s.' % k)
        inst.start()

    # And we wait for them to come up again.

    for k, inst in instances.items():
        print('Waiting for instance %s to come up...' % k)
        inst.wait_until_running()


def ssh_connect(instances):
    print('Connecting to all instances via ssh...')
    clients = {}
    for k, inst in instances.items():
        print('Connecting to %s' % k)
        while True:
            c = paramiko.SSHClient()
            c.load_system_host_keys()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                c.connect(inst.public_ip_address, username='ubuntu',
                          key_filename=KEYFILE)
                clients[k] = c
                print('Connected to %s (%s)' % (k, inst.public_ip_address))
                break
            except:
                print('Failed to connect. Retrying...')
                pass
    return clients


def many_iperf(n, client_transport, server_chan, server_output, instances, addr=None):
    print('IPERF: ', end='')
    sys.stdout.flush()
    if addr is None:
        addr = instances['server'].public_ip_address
    for _ in range(n):
        client_chan = client_transport.open_session()
        client_chan.set_combine_stderr(True)
        client_chan.exec_command(command='iperf3 -c %s -J' % addr)
        print('<', end='')
        sys.stdout.flush()
        while not client_chan.exit_status_ready():
            client_chan.recv(4096)
        client_chan.close()
        print('=', end='')
        sys.stdout.flush()

        while server_chan.recv_ready():
            out = server_chan.recv(4096)
            server_output.write(out)
        print('>', end='')
        sys.stdout.flush()
    print()


def blocking_cmd(ssh, cmd):
    chan = ssh.open_session()
    chan.set_combine_stderr(True)
    chan.exec_command(command=cmd)
    chan.recv_exit_status()


def long_running_cmd(ssh, cmd):
    chan = ssh.open_session()
    chan.set_combine_stderr(True)
    chan.exec_command(command=cmd)
    return chan


def run_exp_mptcp(instances, clients):
    """Runs the AWS experiment, given dict containing AWS instances, and a dict
    containing Paramiko SSH connections to each one.

    You might say this experiment script is hacky, and you would be right. We
    do the experiments in order: first, do control, with one subflow. Then, add
    a NAT detour and use that. Then remove the NAT detour and use a VPN detour.
    The detour daemons can both be run simultaneously with no problems, and
    that's just what we do.

    """
    detour_transport = clients['detour'].get_transport()
    client_transport = clients['client'].get_transport()
    server_transport = clients['server'].get_transport()

    # start detour daemons
    print('Starting detour nat daemon...')
    detour_chan = long_running_cmd(detour_transport, 'cd src; sudo ./nat_detour.py')
    print(detour_chan.recv(4096))

    print('Starting detour vpn daemon...')
    detour_vpn_chan = long_running_cmd(detour_transport, 'cd src; sudo ./vpn_detour.sh')
    print(detour_vpn_chan.recv(4096))

    # start server
    print('Starting iperf server...')
    server_chan = long_running_cmd(server_transport, 'iperf3 -s -J')

    # run iperf several times, recv()ing server output
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances)

    # save control server output
    with open('server.ctrl.mptcp.json', 'wb') as f:
        f.write(server_output.getvalue())

    # send a client daemon config
    print('Sending over the daemon configs...')
    sftp = clients['client'].open_sftp()
    nat_cfg = NAT_CFG % instances['detour'].public_ip_address
    vpn_cfg = VPN_CFG % instances['detour'].public_ip_address
    sftp.putfo(BytesIO(nat_cfg.encode('utf8')),
               '/home/ubuntu/etc/daemon-nat-aws.conf')
    sftp.putfo(BytesIO(vpn_cfg.encode('utf8')),
               '/home/ubuntu/etc/daemon-vpn-aws.conf')
    sftp.close()

    # run the client daemon
    print('Starting up the nat daemon...')
    client_daemon_chan = long_running_cmd(
        client_transport,
        'cd src; sudo ./client daemon ../etc/daemon-nat-aws.conf',
    )

    # run nat trials
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances)

    # save nat server output
    with open('server.nat.mptcp.json', 'wb') as f:
        f.write(server_output.getvalue())

    # kill nat client daemon
    print('Killing daemon...')
    blocking_cmd(client_transport, "sudo pkill -f '^./client daemon'")

    # remove the NAT entry so that the vpn one will be used. not strictly
    # necessary because the vpn should be preferred, but it makes me feel
    # better.
    print('Cleaning up NAT entry...')
    blocking_cmd(client_transport, 'cd src; sudo ./client del %s %d %s %d' %
                 (instances['detour'].public_ip_address, 5201,
                  instances['server'].public_ip_address, 5201))

    # start vpn client daemon
    print('Starting up the openvpn daemon...')
    client_daemon_chan = long_running_cmd(
        client_transport,
        'cd src; sudo ./client daemon ../etc/daemon-vpn-aws.conf',
    )

    # save vpn server output
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances)

    # save vpn output
    with open('server.vpn.mptcp.json', 'wb') as f:
        f.write(server_output.getvalue())

    clients['detour'].close()
    clients['server'].close()
    clients['client'].close()


def run_exp_vanilla(instances, clients):
    """Runs the AWS experiment with vanilla TCP, given dict containing AWS
    instances, and a dict containing Paramiko SSH connections to each one.

    You might say this experiment script is hacky, and you would be right. We
    do the experiments in order: first, do control - TCP across default route.
    Then, add a NAT detour and use that. Then remove the NAT detour and use a
    VPN detour. The detour daemons can both be run simultaneously with no
    problems, and that's just what we do.

    """
    detour_transport = clients['detour'].get_transport()
    client_transport = clients['client'].get_transport()
    server_transport = clients['server'].get_transport()

    # start detour daemons
    print('Starting detour nat daemon...')
    detour_chan = long_running_cmd(detour_transport, 'cd src; sudo ./nat_detour.py')
    print(detour_chan.recv(4096))

    print('Starting detour vpn daemon...')
    detour_vpn_chan = long_running_cmd(detour_transport, 'cd src; sudo ./vpn_detour.sh')
    print(detour_vpn_chan.recv(4096))

    # start server
    print('Starting iperf server...')
    server_chan = long_running_cmd(server_transport, 'iperf3 -s -J')

    # run iperf several times, recv()ing server output
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances)

    # save control server output
    with open('server.ctrl.vanilla.json', 'wb') as f:
        f.write(server_output.getvalue())

    # setup a nat entry
    print('Manually creating a NAT detour...')
    detour_ip = instances['detour'].public_ip_address
    server_ip = instances['server'].public_ip_address
    port = '5201'
    blocking_cmd(client_transport, 'src/request.py %s %s %s %s' % (
        detour_ip, server_ip, port, port))

    # run nat trials, but use the detour IP rather than the server
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances,
               addr=detour_ip)

    # save nat server output
    with open('server.nat.vanilla.json', 'wb') as f:
        f.write(server_output.getvalue())

    # start vpn client daemon
    print('Starting up the openvpn daemon...')
    client_daemon_chan = long_running_cmd(
        client_transport,
        'sudo openvpn --remote %s 1194 udp --client --dev tun '
        '--ca tmp/ca.crt --cert tmp/client1.crt --key tmp/client1.key '
        '--topology p2p --pull --nobind &' % detour_ip,
    )

    print('Waiting for OpenVPN peer address')
    # We need to wait until the openvpn interface is up. This will also
    # give us the peer IP address, which we already configured, but it's
    # always better to dynamically determine.
    output = client_daemon_chan.recv(4096).decode('utf8')
    regexp = re.compile(r'ip addr add dev tun0 local ([0-9.]+) peer ([0-9.]+)')
    while not regexp.search(output):
        output += client_daemon_chan.recv(4096).decode('utf8')
    match = regexp.search(output)
    local, peer = match.groups()

    # Now we configure a specific route so that iperf traffic goes through
    # OpenVPN.
    print('Setting OpenVPN routing rule...')
    blocking_cmd(client_transport,
                 'sudo route add -host %s gw %s' % (server_ip, peer))

    # do vpn trials
    server_output = BytesIO()
    many_iperf(TRIALS, client_transport, server_chan, server_output, instances)

    # save vpn output
    with open('server.vpn.vanilla.json', 'wb') as f:
        f.write(server_output.getvalue())

    clients['detour'].close()
    clients['server'].close()
    clients['client'].close()


def terminate_all(instances):
    for k, inst in instances.items():
        print('Terminating instance %s...' % k)
        inst.terminate()


def cleanup():
    for k in RESOURCE_PARAMS_EACH.keys():
        ec2 = boto3.resource('ec2', **resource_params(k))
        ec2.instances.filter(Filters=TAG_FILTER).terminate()


def main(vanilla=False):
    try:
        instances = create_instances(vanilla)
        first_time_wait(instances)
        clients = ssh_connect(instances)
        if vanilla:
            run_exp_vanilla(instances, clients)
        else:
            run_exp_mptcp(instances, clients)

    except:
        # report it so that debugging is better
        import traceback
        print(traceback.format_exc())

    finally:
        print('Opening ipdb... When you exit, we\'re done here.')
        import ipdb; ipdb.set_trace()
        terminate_all(instances)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        cleanup()
    elif len(sys.argv) > 1 and sys.argv[1] == 'vanilla':
        main(True)
    else:
        main(False)
