"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import GroupNameError, \
    LocaluserLevelError, LocaluserPasswordError, LocaluserNameError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    operation_kwarg, reverse_value_map, config_params)


class LocalUser(object):
    """This class is used to get and handle local user config
    """

    def __init__(self, device, localusername=None):
        self.device = device
        self.local_user_view = 'local-user {0}'.format(localusername)
        self._key_map = {
            'localusername': 'Name',
            'group': 'GroupName',
            'server_ftp': 'FTP',
            'server_http': 'HTTP',
            'server_https': 'HTTPS',
            'server_pad': 'PAD',
            'server_ssh': 'SSH',
            'server_telnet': 'TELNET',
            'server_Terminal': 'Terminal',
            'ftp_dir': 'FTPHomeDir',
            'localspassword': 'Password',
        }
        self._value_map = {}
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

    def get_group_info(self):
        E = data_element_maker()
        top = E.top(
            E.UserAccounts(
                E.UserGroups(
                    E.Group()
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = findall_in_data('Name', nc_get_reply)
        groups = [reply.text for reply in reply_data]
        return groups

    def build_group(self, group=None, stage=False):
        EN = nc_element_maker()
        EC = config_element_maker()
        params = dict(group=group)
        key_map = {
            'group': 'Name',
        }
        config = EN.config(
            EC.top(
                EC.UserAccounts(
                    EC.UserGroups(
                        EC.Group(
                            *config_params(params, key_map)
                        )
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def build_user_level(self, stage=False, **kvargs):
        commands = []
        CMDS = {
            'local_user_level': 'authorization-attribute user-role level-{0}',
        }
        local_user_level = kvargs.get('local_user_level')
        if local_user_level:
            commands.append((CMDS.get('local_user_level')).format(local_user_level))
        if commands:
            commands.insert(0, self.local_user_view)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.UserAccounts(
                E.Management(
                    E.Accounts(
                        E.Account()
                    )
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Account', nc_get_reply)
        if reply_data is None:
            return {}
        return data_elem_to_dict(reply_data, self._key_map, value_map=self._value_map)

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def default(self, stage=False, **params):
        return self._build_config(state='default', stage=stage, **params)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.UserAccounts(
                        EC.Management(
                            EC.Accounts(
                                EC.Account(
                                    *config_params(params, self._key_map, value_map=self._r_value_map)
                                )
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

        if state == 'default':
            EN = nc_element_maker()
            EC = config_element_maker()
            operation = 'delete'
            key_map = {
                'localusername': 'Name',
            }
            config = EN.config(
                EC.top(
                    EC.UserAccounts(
                        EC.Management(
                            EC.Accounts(
                                EC.Account(
                                    *config_params(params, key_map)
                                )
                            )
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

        return False

    def param_check(self, **params):
        group = params.get('group')
        if group:
            if len(group) < 1 or len(group) > 32:
                raise GroupNameError(group)

        local_user_level = params.get('local_user_level')
        if local_user_level:
            if int(local_user_level) < 0 or int(local_user_level) > 15:
                raise LocaluserLevelError(local_user_level)

        localspassword = params.get('localspassword')
        if localspassword:
            if len(localspassword) < 1 or len(localspassword) > 63:
                raise LocaluserPasswordError(localspassword)

        localusername = params.get('localusername')
        if len(localusername) < 1 or len(localusername) > 55:
            raise LocaluserNameError(localusername)
