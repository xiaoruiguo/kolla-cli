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
import logging
import os
import subprocess
import tarfile
import tempfile
import traceback

from kollacli.ansible.inventory import Inventory
from kollacli.ansible.properties import AnsibleProperties
from kollacli.exceptions import CommandError
from kollacli.utils import get_admin_user
from kollacli.utils import get_kolla_etc
from kollacli.utils import get_kolla_home
from kollacli.utils import get_kolla_log_dir
from kollacli.utils import get_kollacli_etc
from kollacli.utils import get_kollacli_home
from kollacli.utils import run_cmd

class AnsiblePlaybook(object):
    playbook_path = ''
    extra_vars = ''
    include_globals = True
    include_passwords = True
    print_output = True
    verbose_level = 0

    log = logging.getLogger(__name__)

    def run(self):
        globals_string = None
        password_string = None
        cmd = ''
        try:
            flag = ''
            # verbose levels: 1=not verbose, 2=more verbose
            if self.verbose_level > 1:
                flag = '-vvv'

            kollacli_home = get_kollacli_home()
            kolla_home = get_kolla_home()
            kolla_etc = get_kolla_etc()
            admin_user = get_admin_user()
            command_string = ('/usr/bin/sudo -u %s ansible-playbook %s'
                              % (admin_user, flag))
            inventory_string = '-i ' + os.path.join(kollacli_home,
                                                    'tools',
                                                    'json_generator.py')
            cmd = (command_string + ' ' + inventory_string)

            if self.include_globals:
                globals_string = self._get_globals_path()
                cmd = (cmd + ' ' + globals_string)

            if self.include_passwords:
                password_string = self._get_password_path()
                cmd = (cmd + ' ' + password_string)

            cmd = (cmd + ' ' + self.playbook_path)

            if self.extra_vars:
                cmd = (cmd + ' ' + self.extra_vars)

            if self.verbose_level > 1:
                # log the ansible command
                self.log.debug('cmd:' + cmd)

                if self.verbose_level > 2:
                    # log the inventory
                    dbg_gen = os.path.join(kollacli_home, 'tools',
                                           'json_generator.py')
                    (inv, _) = \
                            subprocess.Popen(dbg_gen.split(' '),
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE).communicate()
                    self.log.debug(inv)

            err_flag, _ = run_cmd(cmd, self.print_output)
            if err_flag:
                raise Exception('failure')

            self.log.info('success')
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())

    def _get_globals_path(self):
        kolla_etc = get_kolla_etc()
        return (' -e @' + os.path.join(kolla_etc, 'globals.yml '))

    def _get_password_path(self):
        kolla_etc = get_kolla_etc()
        return (' -e @' + os.path.join(kolla_etc, 'passwords.yml '))
