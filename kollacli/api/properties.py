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
import logging

import kollacli.i18n as u

from kollacli.api.exceptions import InvalidArgument
from kollacli.common.properties import AnsibleProperties
from kollacli.common.utils import check_arg
from kollacli.common.utils import safe_decode

LOG = logging.getLogger(__name__)

GLOBAL_TYPE = 'global'
GROUP_TYPE = 'group'
HOST_TYPE = 'host'
PROP_TYPES = [GLOBAL_TYPE, GROUP_TYPE, HOST_TYPE]


class PropertyApi(object):

    class Property(object):
        """Property

        Members:
            - name (str): key
            - value (str): value
            - file_name (str): name of file property is from
            - overrides (bool): does the property override some other value
            - orig_value (str): the value which is overridden or None
            - target (str): group or host name for group or host properties
            - prop_type (str): one of 'global', 'group' or 'host'
            - ovr_global (bool): true if property is overridden at global level
            - ovr_group (bool): true if property is overridden at group level
            - ovr_host (bool): true if property is overridden at host level
        """
        def __init__(self, ansible_property, override_flags):
            self.name = ansible_property.name
            self.value = ansible_property.value
            self.file_name = ansible_property.file_name
            self.overrides = ansible_property.overrides
            self.orig_value = ansible_property.orig_value
            self.target = ansible_property.target
            self.prop_type = ansible_property.prop_type

            if override_flags is not None:
                self.ovr_global = override_flags.ovr_global
                self.ovr_group = override_flags.ovr_group
                self.ovr_host = override_flags.ovr_host
            else:
                self.ovr_global = False
                self.ovr_group = False
                self.ovr_host = False

    def property_set(self, property_dict,
                     property_type=GLOBAL_TYPE, change_set=None):
        """Set a property

        :param property_dict: property dictionary containing key / values
        :type property_dict: dictionary
        :param property_type: one of 'global', 'group' or 'host'
        :type property_type: string
        :param change_set: for group or host sets this is the list of groups
                           or hosts to set the property for
        :type change_set: list of strings

        """
        for key, value in property_dict.items():
            check_arg(key, u._('Property Key'), str)
            check_arg(value, u._('Property Value'), str, empty_ok=True)
            if '"' in value:
                raise InvalidArgument(u._('Cannot use double quotes in '
                                          'a property value.'))
        property_dict = safe_decode(property_dict)

        self._check_type(property_type)
        if property_type is not GLOBAL_TYPE:
            check_arg(change_set, u._('Change Set'), list, none_ok=True)
            change_set = safe_decode(change_set)

        ansible_properties = AnsibleProperties()

        if property_type == GLOBAL_TYPE:
            ansible_properties.set_property(property_dict)
        elif property_type == GROUP_TYPE:
            ansible_properties.set_group_property(property_dict, change_set)
        else:
            ansible_properties.set_host_property(property_dict, change_set)

    def property_clear(self, property_list, property_type=GLOBAL_TYPE,
                       change_set=None):
        """Clear a property

        :param property_list: property list
        :type property_list: list
        :param property_type: one of 'global', 'group' or 'host'
        :type property_type: string
        :param change_set: for group or host clears this is the list of
                           groups or hosts to clear the property for
        :type change_set: list of strings

        """
        check_arg(property_list, u._('Property List'), list)
        property_list = safe_decode(property_list)

        self._check_type(property_type)
        if property_type is not GLOBAL_TYPE:
            check_arg(change_set, u._('Change Set'), list, none_ok=True)
            change_set = safe_decode(change_set)

        ansible_properties = AnsibleProperties()

        if property_type == GLOBAL_TYPE:
            ansible_properties.clear_property(property_list)
        elif property_type == GROUP_TYPE:
            ansible_properties.clear_group_property(property_list, change_set)
        else:
            ansible_properties.clear_host_property(property_list, change_set)

    def property_get(self, property_type=GLOBAL_TYPE, get_set=None):
        """Returns a list of Property objects

        :param property_type: one of 'global', 'group', or 'host'
        :type property_type: string
        :param get_set: optional list of hosts or groups to be used when
                         getting group or host related property lists
        :type get_set: list of strings
        :return: properties
        :rtype: list of Property objects
        """
        self._check_type(property_type)
        get_set = safe_decode(get_set)

        ansible_properties = AnsibleProperties()

        property_list = []
        result_list = []
        if property_type == GLOBAL_TYPE:
            property_list = ansible_properties.get_all_unique()
        elif property_type == GROUP_TYPE:
            property_list = ansible_properties.get_group_list(get_set)
        else:
            property_list = ansible_properties.get_host_list(get_set)

        override_flags = ansible_properties.get_all_override_flags()

        for prop in property_list:
            result = self.Property(prop, override_flags.get(prop.name, None))
            result_list.append(result)

        return result_list

    def _check_type(self, property_type):
        if property_type is None or property_type not in PROP_TYPES:
            raise InvalidArgument(u._('Property Type ({value} is not one of '
                                      'global, group or host')
                                  .format(value=property_type))
