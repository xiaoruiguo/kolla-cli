# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import argparse
import getpass
import logging
import os
import subprocess
import traceback
import utils

from kollacli.ansible.inventory import Inventory
from kollacli.ansible.playbook import AnsiblePlaybook
from kollacli.ansible import properties
from kollacli.exceptions import CommandError
from kollacli.utils import convert_to_unicode
from kollacli.utils import get_admin_user
from kollacli.utils import get_kollacli_home
from kollacli.utils import get_setup_user
from kollacli.utils import run_cmd

from cliff.command import Command
from cliff.lister import Lister


def _host_not_found(log, hostname):
    raise CommandError(
        'Host (%s) not found. ' % hostname +
        'Please add it with "host add"')


class HostAdd(Command):
    """Add host to open-stack-kolla"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostAdd, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>',
                            help='host name or ip address')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = utils.convert_to_unicode(hostname)

            inventory = Inventory.load()
            inventory.add_host(hostname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostDestroy(Command):
    """Destroy

    Stops and removes all kolla related docker containers on either the
    specified host or if no host is specified, on all hosts.
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostDestroy, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname | all>',
                            help='host name or ip address or "all"')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = ''
            hostname = parsed_args.hostname.strip()
            hostname = convert_to_unicode(hostname)

            if hostname != 'all':
                inventory = Inventory.load()
                host = inventory.get_host(hostname)
                if not host:
                    _host_not_found(self.log, hostname)

            self.log.info('please be patient as this may take a while.')
            ansible_properties = properties.AnsibleProperties()
            base_distro = \
                ansible_properties.get_property('kolla_base_distro')
            install_type = \
                ansible_properties.get_property('kolla_install_type')
            container_prefix = base_distro + '-' + install_type
            kollacli_home = get_kollacli_home()
            playbook = AnsiblePlaybook()
            playbook.playbook_path = os.path.join(kollacli_home,
                                                 'ansible/host_destroy.yml')
            playbook.extra_vars = ' --extra-vars \"hosts=' + hostname + \
                                  ' prefix=' + container_prefix + '\"'
            playbook.print_output = False
            playbook.verbose_level = self.app.options.verbose_level
            playbook.run()
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostRemove(Command):
    """Remove host from openstack-kolla"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostRemove, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='host name')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = utils.convert_to_unicode(hostname)
            inventory = Inventory.load()
            inventory.remove_host(hostname)
            Inventory.save(inventory)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostList(Lister):
    """List hosts and their groups

    If a hostname is provided, only list information about that host.
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostList, self).get_parser(prog_name)
        parser.add_argument('hostname', nargs='?', metavar='[hostname]',
                            help='hostname')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = None
            if parsed_args.hostname:
                hostname = parsed_args.hostname.strip()
                hostname = utils.convert_to_unicode(hostname)

            inventory = Inventory.load()

            if hostname:
                host = inventory.get_host(hostname)
                if not host:
                    _host_not_found(self.log, hostname)

            data = []
            host_groups = inventory.get_host_groups()
            if host_groups:
                if hostname:
                    data.append((hostname, host_groups[hostname]))
                else:
                    for (hostname, groupnames) in host_groups.items():
                        data.append((hostname, groupnames))
            else:
                data.append(('', ''))
            return (('Host', 'Groups'), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostCheck(Command):
    """Check if openstack-kollacli is setup"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostCheck, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = utils.convert_to_unicode(hostname)
            inventory = Inventory.load()
            host = inventory.get_host(hostname)
            if not host:
                _host_not_found(self.log, hostname)

            host.check()
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())


class HostSetup(Command):
    """Setup openstack-kollacli on host"""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(HostSetup, self).get_parser(prog_name)
        parser.add_argument('hostname', metavar='<hostname>', help='hostname')
        parser.add_argument('--insecure', nargs='?', help=argparse.SUPPRESS)
        return parser

    def take_action(self, parsed_args):
        try:
            hostname = parsed_args.hostname.strip()
            hostname = utils.convert_to_unicode(hostname)
            setup_user = get_setup_user()
            inventory = Inventory.load()
            host = inventory.get_host(hostname)
            if not host:
                _host_not_found(self.log, hostname)
                return False

            check_ok = host.check(True)
            if check_ok:
                self.log.info('Skipping setup of host (%s) as check is ok'
                              % host.name)
                return True

            if parsed_args.insecure:
                password = parsed_args.insecure.strip()
            else:
                password = getpass.getpass('%s password for %s: ' %
                                           (setup_user, hostname))
            password = utils.convert_to_unicode(password)
            host.setup(password)
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())
