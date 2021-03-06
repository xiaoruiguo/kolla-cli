# Copyright(c) 2016, Oracle and/or its affiliates.  All Rights Reserved.
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
"""Exception definitions."""
import kolla_cli.i18n as u


class CommandError(Exception):
    """CLI command error"""
    def __init__(self, message, *args):
        prefix = u._('ERROR: ')
        if not message.startswith(prefix):
            message = prefix + message
        super(CommandError, self).__init__(message, *args)
