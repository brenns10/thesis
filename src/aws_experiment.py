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
import collections
import sys
from io import BytesIO
from os.path import abspath
from os.path import dirname
from os.path import join
from pprint import pprint

import boto3
import paramiko


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
  logfile = "daemon-nat.log";
  loglevel = "DEFAULT";
}
'''

# Key Pair Name. Hopefully you named it the same thing in every region.
KEYPAIR = 'stephen@greed'
KEYFILE = '/home/stephen/.ssh/id_rsa'

# The filename of the AWS setup script.
SETUP_SCRIPT = join(dirname(abspath(__file__)), '../etc/aws_exp_setup.sh')

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
    'InstanceType': 't2.micro',
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
    #pprint(v)
    return v


def create_instances_params(k):
    v = merge(CREATE_INSTANCES_PARAMS, CREATE_INSTANCES_PARAMS_EACH[k])
    #pprint(v)
    return v


def create_instances():
    instances = {}
    for k in RESOURCE_PARAMS_EACH.keys():
        print('Creating instance %s...' % k)
        resource = boto3.resource('ec2', **resource_params(k))
        instance = resource.create_instances(**create_instances_params(k))
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


def many_iperf(n, client_transport, server_chan, server_output, instances):
    print('IPERF: ', end='')
    sys.stdout.flush()
    for _ in range(n):
        client_chan = client_transport.open_session()
        client_chan.set_combine_stderr(True)
        client_chan.exec_command(command='iperf3 -c %s -J' %
                                 instances['server'].public_ip_address)
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


def run_exp_nat(instances, clients):
    detour_transport = clients['detour'].get_transport()
    client_transport = clients['client'].get_transport()
    server_transport = clients['server'].get_transport()

    # start detour daemon
    print('Starting detour daemon...')
    detour_chan = detour_transport.open_session()
    detour_chan.set_combine_stderr(True)
    detour_chan.exec_command(command='cd src; sudo ./nat_detour.py')
    print(detour_chan.recv(4096))

    # start server
    print('Starting iperf server...')
    server_chan = server_transport.open_session()
    server_chan.set_combine_stderr(True)
    server_chan.exec_command(command='iperf3 -s -J')

    # run iperf several times, recv()ing server output
    server_output = BytesIO()
    many_iperf(30, client_transport, server_chan, server_output, instances)

    # save control server output
    with open('server.ctrl.json', 'wb') as f:
        f.write(server_output.getvalue())

    # send a client daemon config
    print('Sending over the daemon config...')
    sftp = clients['client'].open_sftp()
    nat_cfg = NAT_CFG % instances['detour'].public_ip_address
    vpn_cfg = VPN_CFG % instances['detour'].public_ip_address
    sftp.putfo(BytesIO(nat_cfg.encode('utf8')),
               '/home/ubuntu/etc/daemon-nat-aws.conf')
    sftp.putfo(BytesIO(vpn_cfg.encode('utf8')),
               '/home/ubuntu/etc/daemon-vpn-aws.conf')
    sftp.close()

    # run the client daemon
    print('Starting up the client daemon...')
    client_daemon_chan = client_transport.open_session()
    client_daemon_chan.get_pty() # so we can SIGHUP it
    client_daemon_chan.set_combine_stderr(True)
    client_daemon_chan.exec_command(
        command='cd src; sudo ./client daemon ../etc/daemon-nat-aws.conf'
    )

    server_output = BytesIO()
    many_iperf(30, client_transport, server_chan, server_output, instances)

    # save nat server output
    with open('server.nat.json', 'wb') as f:
        f.write(server_output.getvalue())

    # kill the client daemon and start a vpn one
    client_daemon_chan.close()
    client_daemon_chan = client_transport.open_session()
    client_daemon_chan.set_combine_stderr(True)
    client_daemon_chan.exec_command(
        command='cd src; sudo ./client daemon ../etc/daemon-vpn-aws.conf'
    )

    server_output = BytesIO()
    many_iperf(30, client_transport, server_chan, server_output, instances)

    # save vpn output
    with open('server.vpn.json', 'wb') as f:
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


def main():
    instances = create_instances()
    first_time_wait(instances)
    clients = ssh_connect(instances)
    run_exp_nat(instances, clients)
    print('Opening ipdb... When you exit, we\'re done here.')
    import ipdb; ipdb.set_trace()
    terminate_all(instances)



if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        cleanup()
    else:
        main()
