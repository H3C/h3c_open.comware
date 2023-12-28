"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    HwtacacsParamsError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import reverse_value_map, \
    data_element_maker, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker, \
    config_params, operation_kwarg


class Hwtacacs(object):
    """This class is used to get and handle hwtacacs config
    """

    def __init__(self, device, hwtacacs_scheme_name=None, priority=None):
        self.device = device
        if priority:
            self.priority = priority
        if hwtacacs_scheme_name:
            self.hwtacacs_scheme_name = hwtacacs_scheme_name
        self.hwtacacs_scheme_view = 'hwtacacs scheme {0}'.format(hwtacacs_scheme_name)
        self._key_map = {
            'hwtacacs_scheme_name': 'SchemeName',
        }
        self._value_map = {}
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.Tacacs(
                E.Schemes(
                    E.Scheme()
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Scheme', nc_get_reply)
        if reply_data is None:
            return {}
        return data_elem_to_dict(reply_data, self._key_map, value_map=self._value_map)

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def build_host_name_ip(self, stage=False, **kvargs):
        commands = []
        cmds = {
            'auth_host_name': '{0} authentication {1} {2}',
            'auth_host_ip': '{0} authentication {1} {2}',
            'author_host_name': '{0} authorization {1} {2}',
            'author_host_ip': '{0} authorization {1} {2}',
            'acct_host_name': '{0} accounting {1} {2}',
            'acct_host_ip': '{0} accounting {1} {2}',
        }
        auth_host_name = kvargs.get('auth_host_name')
        auth_host_ip = kvargs.get('auth_host_ip')
        author_host_name = kvargs.get('author_host_name')
        author_host_ip = kvargs.get('author_host_ip')
        acct_host_name = kvargs.get('acct_host_name')
        acct_host_ip = kvargs.get('acct_host_ip')
        auth_host_port = kvargs.get('auth_host_port')
        author_host_port = kvargs.get('author_host_port')
        acct_host_port = kvargs.get('acct_host_port')

        if auth_host_name:
            commands.append((cmds.get('auth_host_name')).format(self.priority, auth_host_name, auth_host_port))
        if auth_host_ip:
            commands.append((cmds.get('auth_host_ip')).format(self.priority, auth_host_ip, auth_host_port))
        if author_host_name:
            commands.append((cmds.get('author_host_name')).format(self.priority, author_host_name, auth_host_port))
        if author_host_ip:
            commands.append((cmds.get('author_host_ip')).format(self.priority, author_host_ip, author_host_port))
        if acct_host_name:
            commands.append((cmds.get('acct_host_name')).format(self.priority, acct_host_name, auth_host_port))
        if acct_host_ip:
            commands.append((cmds.get('acct_host_ip')).format(self.priority, acct_host_ip, acct_host_port))
        if commands:
            commands.insert(0, self.hwtacacs_scheme_view)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def default(self, stage=False, **params):
        return self._build_config(state='default', stage=stage, **params)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.Tacacs(
                        EC.Schemes(
                            EC.Scheme(
                                *config_params(params, self._key_map, value_map=self._r_value_map)
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
                'hwtacacs_scheme_name': 'SchemeName',
            }
            config = EN.config(
                EC.top(
                    EC.Tacacs(
                        EC.Schemes(
                            EC.Scheme(
                                *config_params(params, key_map)
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

    @staticmethod
    def param_check(**params):
        auth_host_name = params.get('auth_host_name')
        auth_host_ip = params.get('auth_host_ip')
        author_host_name = params.get('author_host_name')
        author_host_ip = params.get('author_host_ip')
        acct_host_name = params.get('acct_host_name')
        acct_host_ip = params.get('acct_host_ip')
        auth_host_port = params.get('auth_host_port')
        author_host_port = params.get('author_host_port')
        acct_host_port = params.get('acct_host_port')

        if auth_host_name:
            if auth_host_ip:
                raise HwtacacsParamsError(auth_host_ip)
        if author_host_name:
            if author_host_ip:
                raise HwtacacsParamsError(author_host_ip)
        if acct_host_name:
            if acct_host_ip:
                raise HwtacacsParamsError(acct_host_ip)
        if auth_host_name:
            if len(auth_host_name) < 1 or len(auth_host_name) > 253:
                raise HwtacacsParamsError(auth_host_name)
        if auth_host_port:
            if int(auth_host_port) < 1 or int(auth_host_port) > 65535:
                raise HwtacacsParamsError(auth_host_port)
        if author_host_port:
            if int(author_host_port) < 1 or int(author_host_port) > 65535:
                raise HwtacacsParamsError(author_host_port)
        if acct_host_port:
            if int(acct_host_port) < 1 or int(acct_host_port) > 65535:
                raise HwtacacsParamsError(acct_host_port)
