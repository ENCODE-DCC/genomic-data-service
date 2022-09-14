import argparse
import getpass
import re
import subprocess
import sys
import os
from os.path import expanduser
import boto3

DEMO_CONFIG = ':deploy/cloud-config-demo.yml'
MAIN_MACHINE_CONFIG = ':deploy/cloud-config-gds.yml'
ES_MACHINE_CONFIG = ':deploy/cloud-config-es.yml'
DEMO_INDEXER_USER = 'indexer'
DEMO_INDEXER_PASSWORD = os.environ['DEMO_INDEXER_PASSWORD']
DEMO_MACHINE = 'demo'
MAIN_MACHINE = 'gds'
REGULOME_ES_MACHINE = 'regulome_es'
ENCODE_ES_MACHINE = 'encode_es'
VPC_ID = 'vpc-b7ab4ed1'
SECURITY_GROUPS = ['sg-03506766d1d93e1e7']


def nameify(in_str):
    name = ''.join(c if c.isalnum()
                   else '-' for c in in_str.lower()).strip('-')
    return re.subn(r'\-+', '-', name)[0]


def tag_ec2_instance(instance, tag_data):
    tags = [
        {'Key': 'Name', 'Value': tag_data['name']},
        {'Key': 'branch', 'Value': tag_data['branch']},
        {'Key': 'commit', 'Value': tag_data['commit']},
        {'Key': 'started_by', 'Value': tag_data['username']},
    ]
    instance.create_tags(Tags=tags)
    return instance


def read_ssh_key():
    home = expanduser('~')
    ssh_key_path = home + '/' + '.ssh/id_rsa.pub'
    ssh_keygen_args = ['ssh-keygen', '-l', '-f', ssh_key_path]
    fingerprint = subprocess.check_output(
        ssh_keygen_args).decode('utf-8').strip()
    if fingerprint:
        with open(ssh_key_path, 'r') as key_file:
            ssh_pub_key = key_file.readline().strip()
            return ssh_pub_key
    return None


def _get_bdm(main_args):
    return [
        {
            'DeviceName': '/dev/sda1',
            'Ebs': {
                'VolumeSize': int(main_args.volume_size),
                'VolumeType': 'gp3',
                'DeleteOnTermination': True,
            },
        },
        {
            'DeviceName': '/dev/sdb',
            'NoDevice': '',
        },
        {
            'DeviceName': '/dev/sdc',
            'NoDevice': '',
        },
    ]


def get_user_data(commit, config_file, data_insert, main_args):
    cmd_list = ['git', 'show', commit + config_file]
    config_template = subprocess.check_output(cmd_list).decode('utf-8')
    ssh_pub_key = read_ssh_key()
    if not ssh_pub_key:
        print(
            'WARNING: User is not authorized with ssh access to '
            'new instance because they have no ssh key'
        )
    data_insert['LOCAL_SSH_KEY'] = ssh_pub_key
    # aws s3 authorized_keys folder
    auth_base = 's3://regulome-conf-prod/ssh-keys'
    auth_type = 'prod'
    if main_args.profile_name != 'production':
        auth_type = 'demo'
    auth_keys_dir = '{auth_base}/{auth_type}-authorized_keys'.format(
        auth_base=auth_base,
        auth_type=auth_type,
    )
    data_insert['S3_AUTH_KEYS'] = auth_keys_dir
    data_insert['REDIS_PORT'] = main_args.redis_port
    data_insert['DEMO_INDEXER_USER'] = DEMO_INDEXER_USER
    data_insert['DEMO_INDEXER_PASSWORD'] = DEMO_INDEXER_PASSWORD

    user_data = config_template % data_insert
    return user_data


def _get_instances_tag_data(main_args, ec2_name=None):
    instances_tag_data = {
        'branch': main_args.branch,
        'commit': main_args.commit,
        'name': main_args.name,
        'username': main_args.username,
    }

    if instances_tag_data['name'] is None:
        instances_tag_data['name'] = nameify(
            '%s-%s-%s-%s'
            % (
                instances_tag_data['branch'],
                instances_tag_data['commit'],
                ec2_name,
                instances_tag_data['username'],
            )
        )
    return instances_tag_data


def _get_ec2_client(main_args):
    session = boto3.Session(
        region_name='us-west-2', profile_name=main_args.profile_name
    )
    ec2 = session.resource('ec2')
    return ec2


def _get_run_args(main_args, instances_tag_data, ec2_name=None):
    master_user_data = None
    security_groups = ['ssh-http-https']
    iam_role = 'regulome-instance'
    count = 1
    data_insert = {
        'COMMIT': instances_tag_data['commit'],
        'ROLE': main_args.role,
        'GIT_REPO': main_args.git_repo,
        'REDIS_IP': main_args.redis_ip,
        'REDIS_PORT': main_args.redis_port,
    }
    config_file = DEMO_CONFIG
    if ec2_name == MAIN_MACHINE:
        config_file = MAIN_MACHINE_CONFIG
    elif ec2_name == REGULOME_ES_MACHINE or ec2_name == ENCODE_ES_MACHINE:
        config_file = ES_MACHINE_CONFIG
    user_data = get_user_data(
        instances_tag_data['commit'], config_file, data_insert, main_args
    )
    run_args = {
        'count': count,
        'iam_role': iam_role,
        'user_data': user_data,
        'security_groups': security_groups,
    }
    if master_user_data:
        run_args['master_user_data'] = master_user_data
    return run_args


def _wait_and_tag_instances(
    main_args, run_args, instances_tag_data, instances, cluster_master=False
):
    tmp_name = instances_tag_data['name']
    domain = 'production' if main_args.profile_name == 'production' else 'instance'
    for i, instance in enumerate(instances):
        instances_tag_data['name'] = tmp_name
        print('%s.%s.regulomedb.org' %
              (instance.id, domain))  # Instance:i-34edd56f
        instance.wait_until_exists()
        tag_ec2_instance(instance, instances_tag_data)
        print('Instance ready')


def create_instance(ec2_client, main_args, ec2_name):
    instances_tag_data = _get_instances_tag_data(main_args, ec2_name)
    if instances_tag_data is None:
        sys.exit(10)
    if ec2_client is None:
        sys.exit(20)
    if any(
        ec2_client.instances.filter(
            Filters=[
                {'Name': 'tag:Name', 'Values': [instances_tag_data['name']]},
                {
                    'Name': 'instance-state-name',
                    'Values': ['pending', 'running', 'stopping', 'stopped'],
                },
            ]
        )
    ):
        print('An instance already exists with name: %s' %
              instances_tag_data['name'])
        sys.exit(30)
    run_args = _get_run_args(main_args, instances_tag_data, ec2_name)
    if main_args.dry_run_aws:
        print('Dry Run AWS')
        print('main_args', main_args)
        print('run_args', run_args.keys())
        print('Dry Run AWS')
        sys.exit(30)

    bdm = _get_bdm(main_args)
    instances = ec2_client.create_instances(
        ImageId=main_args.image_id,
        MinCount=run_args['count'],
        MaxCount=run_args['count'],
        InstanceType=main_args.instance_type,
        SecurityGroups=run_args['security_groups'],
        UserData=run_args['user_data'],
        BlockDeviceMappings=bdm,
        InstanceInitiatedShutdownBehavior='terminate',
        IamInstanceProfile={
            'Name': run_args['iam_role'],
        },
        Placement={
            'AvailabilityZone': main_args.availability_zone,
        },
    )
    _wait_and_tag_instances(main_args, run_args, instances_tag_data, instances)
    return instances


def create_security_group(ec2_client, gds_private_ip, main_args):
    cidr_ip = gds_private_ip + '/32'
    group_name = main_args.branch + '-' + main_args.commit + '-' + main_args.username
    try:
        security_group = ec2_client.create_security_group(
            GroupName=group_name, Description=group_name, VpcId=VPC_ID
        )
        security_group_id = security_group.group_id
        print('Security Group Created %s in vpc %s.' %
              (security_group_id, VPC_ID))

        security_group.authorize_ingress(
            DryRun=False,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 9201,
                    'ToPort': 9201,
                    'IpRanges': [{'CidrIp': cidr_ip}],
                }
            ],
        )
        return security_group
    except Exception as e:
        print('fail to create security group:', e)
        return None


def main():
    # Gather Info
    main_args = parse_args()
    ec2_client = _get_ec2_client(main_args)
    if main_args.demo:
        create_instance(ec2_client, main_args, DEMO_MACHINE)
    elif main_args.es == 'regulome':
        create_instance(ec2_client, main_args, REGULOME_ES_MACHINE)
    elif main_args.es == 'encode':
        create_instance(ec2_client, main_args, ENCODE_ES_MACHINE)
    else:
        instances_gds = create_instance(ec2_client, main_args, MAIN_MACHINE)
        security_group_id = None
        for i, instance in enumerate(instances_gds):
            gds_private_ip = instance.private_ip_address
            security_group = create_security_group(
                ec2_client, gds_private_ip, main_args)
            security_group_id = security_group.group_id
            SECURITY_GROUPS.append(security_group_id)
            instance.modify_attribute(Groups=SECURITY_GROUPS)

        instances_regluome_es = create_instance(
            ec2_client, main_args, REGULOME_ES_MACHINE)
        for i, instance in enumerate(instances_regluome_es):
            instance.modify_attribute(Groups=SECURITY_GROUPS)
        instances_encode_es = create_instance(
            ec2_client, main_args, ENCODE_ES_MACHINE)
        for i, instance in enumerate(instances_encode_es):
            instance.modify_attribute(Groups=SECURITY_GROUPS)


def parse_args():
    def check_region_index(value):
        lower_value = value.lower()
        allowed_values = ['true', 't', 'false', 'f']
        if value.lower() not in allowed_values:
            raise argparse.ArgumentTypeError(
                "Noncase sensitive argument '%s' is not in [%s]."
                % (
                    str(value),
                    ', '.join(allowed_values),
                )
            )
        if lower_value[0] == 't':
            return 'True'
        return 'False'

    def check_volume_size(value):
        allowed_values = ['120', '200', '500']
        if not value.isdigit() or value not in allowed_values:
            raise argparse.ArgumentTypeError(
                "%s' is not in [%s]."
                % (
                    str(value),
                    ', '.join(allowed_values),
                )
            )
        return value

    def hostname(value):
        if value != nameify(value):
            raise argparse.ArgumentTypeError(
                '%r is an invalid hostname, only [a-z0-9] and hyphen allowed.' % value
            )
        return value

    parser = argparse.ArgumentParser(
        description='Deploy Genomic Data Service on AWS',
    )
    parser.add_argument('-b', '--branch', default=None,
                        help='Git branch or tag')
    parser.add_argument('-n', '--name', type=hostname, help='Instance name')
    parser.add_argument(
        '--dry-run-aws', action='store_true', help='Abort before ec2 requests.'
    )
    parser.add_argument(
        '--image-id',
        default='ami-0f02ec44da36ff919',
        help=('Ubuntu 20.04 AMI with require dependencies'),
    )
    parser.add_argument(
        '--instance-type', default='r5.2xlarge', help='AWS Instance type'
    )
    parser.add_argument('--profile-name', default='regulome',
                        help='AWS creds profile')
    parser.add_argument('--redis-ip', default='localhost', help='Redis IP.')
    parser.add_argument('--redis-port', default=6379, help='Redis Port.')
    parser.add_argument(
        '--volume-size',
        default=500,
        type=check_volume_size,
        help='Size of disk. Allowed values 120, 200, and 500',
    )
    parser.add_argument(
        '--availability-zone', default='us-west-2a', help='Set EC2 availabilty zone'
    )
    parser.add_argument(
        '--git-repo',
        default='https://github.com/ENCODE-DCC/genomic-data-service.git',
        help='Git repo to checkout branches: https://github.com/{user|org}/{repo}.git',
    )
    parser.add_argument('--demo', action='store_true',
                        help='Deploy a demo for RegulomDB')

    parser.add_argument('--es', default=None, choices=[None, 'regulome', 'encode'],
                        help='specify if the elasticsearch server is for RegulomeDB or Encode')

    args = parser.parse_args()
    if not args.branch:
        args.branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
        ).decode('utf-8').strip()
    args.commit = (
        subprocess.check_output(
            ['git', 'rev-parse', '--short', args.branch]
        )
        .decode('utf-8')
        .strip()
    )
    if not subprocess.check_output(
        ['git', 'branch', '-r', '--contains', args.commit]
    ).strip():
        print(
            'Commit %r not in origin. Did you git push?' % args.commit
        )
        sys.exit(1)
    args.username = getpass.getuser()
    args.role = 'candidate'
    print('Role:', args.role)
    print('Using branch:', args.branch)
    if args.demo:
        print('Deploy demo.')
    return args


if __name__ == '__main__':
    main()
