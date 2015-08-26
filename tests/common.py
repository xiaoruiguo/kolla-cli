# Copyright(c) 2015, Oracle and/or its affiliates.  All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
import logging
import os
import subprocess
import sys
import traceback

import testtools

import kollacli.utils as utils

TEST_SUFFIX = 'test/'
ENV_ETC = 'KOLLA_CLI_ETC'
VENV_PY_PATH = '.venv/bin/python'
KOLLA_CMD = 'kollacli'
KOLLA_SHELL_DIR = 'kollacli'

HOSTS_FNAME = 'test_hosts'


class KollaCliTest(testtools.TestCase):

    cmd_prefix = ''
    log = logging.getLogger(__name__)

    def setUp(self):
        super(KollaCliTest, self).setUp()

        logging.basicConfig(stream=sys.stderr)
        self.log.setLevel(logging.DEBUG)
        self.log.info('Starting test: %s *************************************'
                      % self._testMethodName)

        # switch to test path
        self._setup_env_var()
        etc_path = utils.get_kollacli_etc()
        self.log.debug('etc for tests: %s' % etc_path)

        self._set_cmd_prefix()

        # make sure inventory dirs exists and remove inventory file
        self._init_dir(etc_path)
        etc_ansible_path = os.path.join(etc_path, 'ansible/')
        self._init_dir(etc_ansible_path)
        etc_inventory_path = os.path.join(etc_ansible_path, 'inventory/')
        self._init_dir(etc_inventory_path)
        self._init_file(os.path.join(etc_inventory_path, 'inventory.json'))

    def tearDown(self):
        self._restore_env_var()
        super(KollaCliTest, self).tearDown()

    def run_client_cmd(self, cmd, expect_error=False):
        full_cmd = ('%s %s' % (self.cmd_prefix, cmd))
        self.log.debug('running command: %s' % cmd)
        (retval, msg) = self._run_command(full_cmd)

        if not expect_error:
            self.assertEqual(0, retval, ('command failed: (%s), cmd: %s'
                                         % (msg, full_cmd)))
        return msg

    # PRIVATE FUNCTIONS ----------------------------------------------------
    def _setup_env_var(self):
        etc_path = utils.get_kollacli_etc()
        if not etc_path.endswith(TEST_SUFFIX):
            etc_path = os.path.join(etc_path, TEST_SUFFIX)
            os.environ[ENV_ETC] = etc_path

    def _restore_env_var(self):
        etc_path = utils.get_kollacli_etc()
        if etc_path.endswith(TEST_SUFFIX):
            etc_path = etc_path.rsplit('/', 1)[0]
            os.environ[ENV_ETC] = etc_path

    def _run_command(self, cmd):
        # self.log.debug('run cmd: %s' % cmd)
        retval = 0
        msg = ''
        try:
            msg = subprocess.check_output(cmd.split(),
                                          stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            retval = e.returncode
            msg = e.output

        except Exception as e:
            retval = e.errno
            msg = ('Unexpected exception: %s, cmd: %s'
                   % (traceback.format_exc(), cmd))

        # the py dev debugger adds a string at the line start, remove it
        if msg.startswith('pydev debugger'):
            msg = msg.split('\n', 1)[1]
        return (retval, msg)

    def _init_file(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    def _init_dir(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)

    def _set_cmd_prefix(self):
        """Select the command to invoke the kollacli

            The kolla cli can be run:

            1) from the command line via $ KOLLA_CMD, or

            2) if that doesn't work, this assumes that we're operating
            in a dev't debug environment, which means that the kollacli
            was installed in a virtualenv. So then we have to use the python
            version in virtualenv and the tests will have to be run
            from the tests directory.
        """
        (_, msg) = self._run_command('which python')
        self.log.debug('starting with python: %s' % msg.strip())
        self.cmd_prefix = KOLLA_CMD
        (retval, msg) = self._run_command('%s host add -h' % self.cmd_prefix)
        if retval == 0:
            self.log.debug('%s found, will use as the test command'
                           % KOLLA_CMD)
            return

        # self.log.debug('%s exec failed: %s' % (KOLLA_CMD, msg))
        self.log.debug('look for kollacli shell in virtual env')

        # try to see if this is a debug virtual environment
        # will run the tests via kollacli/shell.sh and
        # use the python in .venv/bin/python
        cwd = os.getcwd()
        if cwd.endswith('tests'):
            os_kolla_dir = cwd.rsplit('/', 1)[0]

            shell_dir = os_kolla_dir + '/%s/' % KOLLA_SHELL_DIR
            shell_path = os.path.join(shell_dir, 'shell.py')

            python_path = os.path.join(os_kolla_dir, VENV_PY_PATH)

            self.log.debug('shell_path: %s' % shell_path)
            self.log.debug('python_path: %s' % python_path)
            if os.path.exists(shell_path) and os.path.exists(python_path):
                self.cmd_prefix = '%s %s ' % (python_path, shell_path)

                self.run_client_cmd('host add -h')
                self.log.info('successfully ran command in venv environment')
                return

        self.assertEqual(0, 1,
                         'no kollacli shell command found. Aborting tests')


class TestHosts(object):
    """host systems for testing

    This class can either be used for metadata to hold info about test hosts,
    or can be loaded from a test file for info on actual test host machines.
    """
    log = logging.getLogger(__name__)

    def __init__(self):
        self.info = {}

    def remove(self, name):
        del self.info[name]

    def add(self, name):
        if name not in self.info:
            self.info[name] = {'groups': [],
                               'pwd': '',
                               }

    def get_groups(self, name):
        return self.info[name]['groups']

    def add_group(self, name, group):
        if group not in self.info[name]['groups']:
            self.info[name]['groups'].append(group)

    def remove_group(self, name, group):
        if group in self.info[name]['groups']:
            self.info[name]['groups'].remove(group)

    def get_hostnames(self):
        return self.info.keys()

    def set_password(self, name, password):
        self.info[name]['pwd'] = password

    def get_password(self, name):
        return self.info[name]['pwd']

    def load(self):
        """load hosts from test_hosts file"""
        path = self.get_test_hosts_path()
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                tokens = line.split()
                if len(tokens) != 3:
                    raise Exception('%s expected 3 params on line: %s'
                                    % (HOSTS_FNAME, line))
                hostname = tokens[0]
                pwd = tokens[2]
                self.add(hostname)
                self.set_password(hostname, pwd)

    def get_test_hosts_path(self):
        """get test_hosts directory"""
        path = ''
        # first check the current directory
        if os.path.exists(HOSTS_FNAME):
            path = os.path.join(os.getcwd(), HOSTS_FNAME)
        else:
            # check the user's home directory
            path = os.path.join(os.path.expanduser('~'), HOSTS_FNAME)
            if not os.path.exists(path):
                raise Exception('test_hosts file not found in current ' +
                                'or home directory')
        return path