"""Manage EVPN on COM7 devices.
author: liudongxue
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import reverse_value_map, \
    nc_element_maker, config_element_maker, \
    config_params, operation_kwarg


class Evpn(object):
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
            'addrfamily': 'AddressFamily',
            'rttype': 'RTType',
            'sessaf': 'SessAF',
            'aftype': 'Type',
            'family': 'Family'
        }

        # used to map value values from our dictionary model
        # to expected XML tags and vice versa
        self._value_map = {
            'AddressFamily': {'1': 'ipv4',
                              '2': 'ipv6',
                              '3': 'vpn',
                              '4': 'evpn'},
            'RTType': {'1': 'import',
                       '2': 'export'},
            'SessAF': {'1': 'ipv4',
                       '3': 'ipv6'},
            'Type': {'1': 'ipv4uni',
                     '2': 'ipv4mul',
                     '3': 'mdt',
                     '4': 'vpnv4',
                     '5': 'ipv6uni',
                     '6': 'ipv6mul',
                     '7': 'vpnv6',
                     '8': 'l2vpn',
                     '9': 'l2vpn_evpn',
                     '10': 'link_state',
                     '11': 'ipv4rtf',
                     '12': 'ipv4mvpn',
                     '13': 'ipv4flosp',
                     '14': 'vpnv4flosp',
                     '15': 'ipv6flosp',
                     '16': 'vpnv6flosp'},
            'Family': {'1': 'ipv4uni',
                       '2': 'ipv4mul',
                       '3': 'mdt',
                       '4': 'vpnv4',
                       '5': 'ipv6uni',
                       '6': 'ipv6mul',
                       '7': 'vpnv6',
                       '8': 'l2vpn',
                       '9': 'l2vpn_evpn',
                       '10': 'link_state',
                       '11': 'ipv4rtf',
                       '12': 'ipv4mvpn',
                       '13': 'ipv4flosp',
                       '14': 'vpnv4flosp',
                       '15': 'ipv6flosp',
                       '16': 'vpnv6flosp'}
        }
        self._VRF = 'VRF'
        self._RTEntry = 'RTEntry'
        self._Ipaddr = 'IpAddress'
        self._Mask = 'Mask'
        self._Asnum = 'ASNumber'
        self._Con_Iface = 'ConnectInterface'

        self._iface_index_name = 'IfIndex'
        self._ipaddress = 'IpAddress'

        self.vrf = ''
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)
        interface = Interface(device, interface_name)
        self.device = device
        self.interface_name, self.iface_type, self.subiface_num = interface._iface_type(interface_name)
        self.iface_index = interface._get_iface_index()
        self.iface_exists = True if self.iface_index != '1' else False
        self.is_ethernet, self.is_routed = interface._is_ethernet_is_routed()
        if self.interface_name != '':
            if self.subiface_num:
                if self.is_routed:
                    self.interface_name = str(self.interface_name + '.' + self.subiface_num)

    def create_evpn(self, stage=False, vrf='ali1', rd='1:1'):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.L3vpn(
                    EC.L3vpnVRF(
                        EC.VRF(
                            EC.VRF(vrf),
                            EC.RD(rd)
                        )
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_evpn_rd(self, stage=False, vrf='ali1'):
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.L3vpn(
                    EC.L3vpnVRF(
                        EC.VRF(
                            EC.VRF(vrf)
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

    def comfigue_evpn_rt(self, stage=False, vrf='ali1', rtentry='30:1', **params):
        params[self._VRF] = vrf
        params[self._RTEntry] = rtentry
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.L3vpn(
                    EC.L3vpnRT(
                        EC.RT(
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

    def remove_evpn_rt(self, stage=False, vrf='ali1', rtentry='30:1', **params):
        params[self._VRF] = vrf
        params[self._RTEntry] = rtentry
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.L3vpn(
                    EC.L3vpnRT(
                        EC.RT(
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

    def create_bgp_instance(self, stage=False, asnum='200'):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.BGP(
                    EC.Instances(
                        EC.Instance(
                            EC.Name(),
                            EC.ASNumber(asnum)
                        )
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_bgp_instance(self, stage=False):
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.BGP(
                    EC.Instances(
                        EC.Instance(
                            EC.Name()
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

    def create_bgp_session(self, stage=False, ipaddr='4.4.4.4', mask='255', asnum='200', **params):
        if self.interface_name != '':
            params[self._Ipaddr] = ipaddr
            params[self._Mask] = mask
            params[self._Asnum] = asnum
            params[self._Con_Iface] = self.interface_name
            params['Name'] = ''
            params['VRF'] = ''
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.BGP(
                        EC.CfgSessions(
                            EC.CfgSession(
                                *config_params(params, self._key_map, value_map=self._r_value_map)
                            )
                        )
                    )
                )
            )
        else:
            params[self._Ipaddr] = ipaddr
            params[self._Mask] = mask
            params[self._Asnum] = asnum
            params['Name'] = ''
            params['VRF'] = ''
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.BGP(
                        EC.CfgSessions(
                            EC.CfgSession(
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

    def entry_bgp_view(self, stage=False, **params):
        params['Name'] = ''
        params['VRF'] = ''
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.BGP(
                    EC.Familys(
                        EC.Family(
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

    def publish_bgp_route(self, stage=False, ipaddr='4.4.4.4', mask='255', **params):
        params[self._Ipaddr] = ipaddr
        params[self._Mask] = mask
        params['Name'] = ''
        params['VRF'] = ''
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.BGP(
                    EC.Neighbors(
                        EC.Neighbor(
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


class EVPN(object):
    def __init__(self, device, asnum, bgp_name, ipaddr, mask, vrf):
        self.device = device
        self.vrf = vrf
        self.asnum = asnum
        self.bgp_name = bgp_name
        self.ipaddr = ipaddr
        self.mask = mask

    def build(self, stage=False, **EVpn):
        return self._build_config_present(state='present', stage=stage, **EVpn)

    def _build_config_present(self, state, stage=False, **EVpn):
        EVpn['vrf'] = self.vrf
        EVpn['asnum'] = self.asnum
        EVpn['bgp_name'] = self.bgp_name
        EVpn['ipaddr'] = self.ipaddr
        EVpn['mask'] = self.mask
        c2 = True
        if state == 'present':
            get_cmd = self._get_cmd(**EVpn)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]

    @staticmethod
    def _get_cmd(**EVpn):
        VRF = EVpn.get('vrf')
        Asnum = EVpn.get('asnum')
        BGP_name = EVpn.get('bgp_name')
        IPaddr = EVpn.get('ipaddr')
        MASK = EVpn.get('mask')

        commands = []
        if BGP_name and VRF:
            cmd_2 = 'bgp {0} instance {1}'.format(BGP_name, VRF)
            commands.append(cmd_2)
        if BGP_name and not VRF:
            cmd_2 = 'bgp {0}'.format(BGP_name)
            commands.append(cmd_2)

        if IPaddr and Asnum and MASK:
            cmd_1 = 'peer {0} {1} as-number {2}'.format(IPaddr, MASK, Asnum)
            commands.append(cmd_1)
        return commands
