"""Manage ntp on COM7 devices.
author: liudongxue
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    nc_element_maker, config_element_maker,
    operation_kwarg, reverse_value_map, config_params)


class Ntp(object):
    """This class is used to build acl configurations on ``COM7`` devices.

    Args:
        device (COM7): connected instance of a
            ``phyp.comware.COM7`` object.
        interface_name (str): The name of the interface.

    Attributes:
        device (COM7): connected instance of a
            ``phyp.comware.COM7`` object.
        interface_name (str): The name of the interface.
    """

    def __init__(self, device, interface_name):
        # used to map key values from our dictionary model
        # to expected XML tags and vice versa
        self._key_map = {
            'service': 'Service',
            'addrtype': 'AddressType',
            'hostmode': 'HostMode'
        }

        # used to map value values from our dictionary model
        # to expected XML tags and vice versa
        self._value_map = {
            'Service': {'1': 'ntp',
                        '2': 'sntp'},
            'AddressType': {'1': 'ipv4',
                            '2': 'ipv6'},
            'HostMode': {'1': 'symactive',
                         '3': 'client'}
        }
        self._key_map_auth = {
            'service': 'Service',
            'authmode': 'AuthMode'
        }

        self._value_map_auth = {
            'Service': {'1': 'ntp',
                        '2': 'sntp'},
            'AuthMode': {'1': 'md5',
                         '2': 'hmac_sha_1',
                         '3': 'hmac_sha_256',
                         '4': 'hmac_sha_384',
                         '5': 'hmac_sha_384'}
        }
        self._key_map_delauth = {
            'service': 'Service'
        }
        self._value_map_delauth = {
            'Service': {'1': 'ntp',
                        '2': 'sntp'}
        }
        # xml tags
        self._keyID = 'KeyID'
        self._Auth_Key = 'AuthKey'
        self._Reliable = 'Reliable'
        self._iface_index_name = 'IfIndex'
        self._ipaddress = 'IpAddress'
        self._vrf = 'VRF'
        self.vrf = ''
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

        self._r_key_map_auth = dict(reversed(item) for item in self._key_map_auth.items())
        self._r_value_map_auth = reverse_value_map(self._r_key_map_auth, self._value_map_auth)
        self._r_key_map_delauth = dict(reversed(item) for item in self._key_map_delauth.items())
        self._r_value_map_delauth = reverse_value_map(self._r_key_map_delauth, self._value_map_delauth)
        interface = Interface(device, interface_name)
        self.device = device
        self.interface_name, self.iface_type, subiface_num = interface._iface_type(interface_name)
        self.iface_index = interface._get_iface_index()
        self.iface_exists = True if self.iface_index != '1' else False

    def enable_ntp(self, stage=False, ntpenable='false', ntpauthenable='false'):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.Service(
                        EC.NTPEnable(ntpenable),
                        EC.NTPAuthEnable(ntpauthenable)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def comfigue_refclock_master(self, stage=False, stratum='2'):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.RefClocks(
                        EC.RefClock(
                            EC.RefID('127.127.1.1'),
                            EC.Stratum(stratum)
                        )
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_refclock_master(self, stage=False):
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.RefClocks(
                        EC.RefClock(
                            EC.RefID('127.127.1.1')
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def create_authentication(self, stage=False, keyid='2', authkey='aNiceKey', reliable='false', **params):
        params[self._keyID] = keyid
        params[self._Auth_Key] = authkey
        params[self._Reliable] = reliable
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.AuthenticationKey(
                        EC.Authentication(
                            *config_params(params, self._key_map_auth, value_map=self._r_value_map_auth)
                        )
                    )
                )
            )
        )

        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_authentication(self, stage=False, keyid='42', **params):
        params[self._keyID] = keyid
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.AuthenticationKey(
                        EC.Authentication(
                            *config_params(params, self._key_map_delauth, value_map=self._r_value_map_delauth)
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )

        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_auth_reliable(self, stage=False, keyid='42', reliable='false', **params):
        params[self._keyID] = keyid
        params[self._Reliable] = reliable
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.AuthenticationKey(
                        EC.Authentication(
                            *config_params(params, self._key_map_delauth, value_map=self._r_value_map_delauth)
                        )
                    )
                )
            )
        )

        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def confiure_ntp_client(self, stage=False, ipadd='10.1.1.1', keyid='42', **params):
        if self.iface_exists:
            params[self._keyID] = keyid
            params[self._iface_index_name] = self.iface_index
            params[self._ipaddress] = ipadd
            params[self._vrf] = self.vrf
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.NTP(
                        EC.Clients(
                            EC.Client(
                                *config_params(params, self._key_map, value_map=self._r_value_map)
                            )
                        )
                    )
                )
            )
        else:
            params[self._keyID] = keyid
            params[self._ipaddress] = ipadd
            params[self._vrf] = self.vrf
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.NTP(
                        EC.Clients(
                            EC.Client(
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

    def remove_ntp_client(self, stage=False, ipadd='10.1.1.1', **params):
        operation = 'delete'
        params[self._ipaddress] = ipadd
        params[self._vrf] = self.vrf
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.NTP(
                    EC.Clients(
                        EC.Client(
                            *config_params(params, self._key_map, value_map=self._r_value_map)
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)
