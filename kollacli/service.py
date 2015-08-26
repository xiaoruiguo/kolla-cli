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
import traceback

from kollacli.ansible.inventory import Inventory
from kollacli.exceptions import CommandError

from cliff.lister import Lister


class ServiceList(Lister):
    """Service List"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        try:
            inventory = Inventory.load()

            data = []
            service_groups = inventory.get_service_groups()
            if service_groups:
                for (servicename, groupnames) in service_groups.items():
                    data.append((servicename, groupnames))
            else:
                data.append(('', ''))
            return (('Service', 'Groups'), sorted(data))
        except CommandError as e:
            raise e
        except Exception as e:
            raise Exception(traceback.format_exc())