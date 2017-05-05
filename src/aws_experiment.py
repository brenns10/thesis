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
from os.path import abspath
from os.path import dirname
from os.path import join
from pprint import pprint

import boto3


# Key Pair Name. Hopefully you named it the same thing in every region.
KEYPAIR = 'stephen@greed'

# The filename of the AWS setup script.
SETUP_SCRIPT = join(dirname(abspath(__file__)), '../etc/aws_exp_setup.sh')

# These tags are applied to everything we create, so it's easier to clean up
# via the Console if things go wrong.
TAGS = [
    {'Key': 'Project', 'Value': 'Thesis'},
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


def terminate_all(instances):
    for k, inst in instances.items():
        print('Terminating instance %s...' % k)
        inst.terminate()

    for k, inst in instances.items():
        print('Waiting for instance %s to terminate...' % k)
        inst.wait_until_terminated()


def main():
    instances = create_instances()
    first_time_wait(instances)
    print('Hit ENTER when you want to terminate them.')
    input()
    terminate_all(instances)


if __name__ == '__main__':
    main()
