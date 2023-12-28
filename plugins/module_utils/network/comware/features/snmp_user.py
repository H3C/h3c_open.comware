"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, find_in_data, data_elem_to_dict, reverse_value_map)


class SnmpUser(object):
    """This class is used to get data and configure a specific usm user.

    """

    def __init__(self, device, usm_user_name=None, user_group=None, security_model=None):
        self.device = device
        if usm_user_name:
            self.usm_user_name = usm_user_name
        if user_group:
            self.user_group = user_group
        if security_model:
            self.security_model = security_model

        # dictionary to XML tag mappings
        self.user_key_map = {
            'usm_user_name': 'Name',
            'security_model': 'SecurityMode',
        }

        self.R_user_key_map = dict(reversed(item) for item in self.user_key_map.items())
        self.value_map = {
            'SecurityMode': {
                '1': 'v1',
                '2': 'v2c',
                '3': 'v3'
            }
        }
        self.R_value_map = reverse_value_map(
            self.R_user_key_map, self.value_map)

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.SNMP(
            E.Users(
                E.User(
                )
            )
        )

        return top

    def get_group_list(self):
        """Get a list of usernames that exist on the switch.

        Returns:
            It returns a list of usernames as strings.
        """
        top = self.gen_top()
        nc_get_reply = self.device.get(('subtree', top))
        user_xml = findall_in_data('Name', nc_get_reply)
        users = [user.text for user in user_xml]

        return users

    def get_config(self):
        """Gets current configuration for a given username

        """
        top = self.gen_top()
        user_comm_ele = find_in_data('User', top)
        user_comm_ele.append(data_element_maker().Name(self.usm_user_name))
        nc_get_reply = self.device.get(('subtree', top))
        snmp_user_config = data_elem_to_dict(nc_get_reply, self.user_key_map, value_map=self.value_map)
        return snmp_user_config

    def user_build(self, stage=True, **user):

        user['usm_user_name'] = self.usm_user_name
        user['user_group'] = self.user_group
        user['security_model'] = self.security_model
        usm_user_name = user.get('usm_user_name')
        user_group = user.get('user_group')
        security_model = user.get('security_model')
        acl_number = user.get('acl_number')
        auth_protocol = user.get('auth_protocol')
        priv_protocol = user.get('priv_protocol')
        auth_key = user.get('auth_key')
        priv_key = user.get('priv_key')

        commands = []
        if security_model != 'v3':
            cmd = 'snmp-agent usm-user {0} {1} {2}'.format(security_model, usm_user_name, user_group)
            if acl_number:
                cmd = cmd + ' acl {0}'.format(acl_number)
            commands.append(cmd)

        else:
            cmd = 'snmp-agent usm-user {0} {1} {2}'.format(security_model, usm_user_name, user_group)
            if auth_protocol and auth_key:
                cmd = cmd + ' simple authentication-mode {0} {1}'.format(auth_protocol, auth_key)
                if priv_protocol and priv_key:
                    cmd = cmd + ' privacy-mode {0} {1}'.format(priv_protocol, priv_key)
            if acl_number:
                cmd = cmd + ' acl {0}'.format(acl_number)
            commands.append(cmd)

        if commands:
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def user_remove(self, stage=True, **user):

        user['usm_user_name'] = self.usm_user_name
        user['security_model'] = self.security_model
        usm_user_name = user.get('usm_user_name')
        security_model = user.get('security_model')

        commands = []
        cmd = ''
        if usm_user_name and security_model:
            cmd = 'undo snmp-agent usm-user {0} {1}'.format(security_model, usm_user_name)
            if security_model == 'v3':
                cmd = cmd + ' local'
        commands.append(cmd)

        if commands:
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)
