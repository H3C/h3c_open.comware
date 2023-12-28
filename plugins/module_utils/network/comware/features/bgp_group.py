"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    BgpParamsError, InstanceParamsError, GroupParamsError, PeerParamsError, BgpMissParamsError)


class Bgp(object):
    """This class is used to get and handle stp config
    """

    def __init__(self, device, bgp_as, instance=None):
        self.device = device
        self.bgp_as = bgp_as
        self.instance = instance

    def get_config(self):
        existing = []
        config = self.device.cli_display('display current-configuration | include bgp')
        bgp_info = config.split('\n')
        for line in bgp_info[1:]:
            if re.search(r'^bgp', line):
                bgp_name = line.split('bgp')[-1].strip(' ')
                existing.append(bgp_name)
        return existing

    def get_group_info(self, group):
        command = 'display current-configuration | include "group {0}"'.format(group)
        config = self.device.cli_display(command)
        group_info = config.split('\n')
        if len(group_info) > 2:
            return True
        else:
            return False

    def remove_bgp(self, stage=False, **kvargs):
        commands = []
        bgp_as = kvargs.get('bgp_as')
        instance = kvargs.get('instance')
        if instance:
            commands.append('undo bgp {0} instance {1}'.format(bgp_as, instance))
        else:
            commands.append('undo bgp {0}'.format(bgp_as))
        commands.append('\n')
        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def build_bgp_group(self, stage=False, **kvargs):
        commands = []
        cmds = {
            'bgp_as': 'bgp {0}',
            'instance': 'bgp {0} instance {1}',
            'group': 'group {0}',
            'group_type': 'group {0} {1}',
            'peer_connect_intf': 'peer {0} connect-interface {1}',
            'peer_in_group': 'peer {0} group {1}',
            'address_family': 'address-family {0}',
            'evpn': 'address-family {0} evpn',
            'policy_vpn_target_T': 'policy vpn-target',
            'policy_vpn_target_F': 'undo policy vpn-target',
            'reflect_client': 'peer {0} reflect-client',
            'peer_group_state': 'peer {0} enable',
        }
        bgp_as = kvargs.get('bgp_as')
        instance = kvargs.get('instance')
        group = kvargs.get('group')
        group_type = kvargs.get('group_type')
        peer = kvargs.get('peer')
        peer_connect_intf = kvargs.get('peer_connect_intf')
        peer_in_group = kvargs.get('peer_in_group')
        address_family = kvargs.get('address_family')
        evpn = kvargs.get('evpn')
        policy_vpn_target = kvargs.get('policy_vpn_target')
        reflect_client = kvargs.get('reflect_client')
        peer_group_state = kvargs.get('peer_group_state')

        if bgp_as and instance is None:
            commands.append((cmds.get('bgp_as')).format(bgp_as))
        if bgp_as and instance:
            commands.append((cmds.get('instance')).format(bgp_as, instance))
        if group and group_type is None:
            commands.append((cmds.get('group')).format(group))
        if group and group_type:
            commands.append((cmds.get('group_type')).format(group, group_type))
        if peer_connect_intf:
            commands.append((cmds.get('peer_connect_intf')).format(peer, peer_connect_intf))
        if peer_in_group:
            commands.append((cmds.get('peer_in_group')).format(peer, peer_in_group))
        if address_family and evpn == 'false':
            commands.append((cmds.get('address_family')).format(address_family))
        if address_family and evpn == 'true':
            commands.append((cmds.get('evpn')).format(address_family, evpn))
        if policy_vpn_target == 'enable':
            commands.append((cmds.get('policy_vpn_target_T')))
        if policy_vpn_target == 'disable':
            commands.append((cmds.get('policy_vpn_target_F')))
        if peer_group_state == 'true':
            commands.append((cmds.get('peer_group_state')).format(peer))
        if reflect_client == 'true':
            commands.append((cmds.get('reflect_client')).format(peer))
        commands.append('\n')

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    @staticmethod
    def param_check(**params):
        """Checks given parameters
        """
        bgp_as = params.get('bgp_as')
        instance = params.get('instance')
        group = params.get('group')
        peer = params.get('peer')
        peer_connect_intf = params.get('peer_connect_intf')
        evpn = params.get('evpn')
        address_family = params.get('address_family')

        if bgp_as:
            if int(bgp_as) < 1 or int(bgp_as) > 4294967295:
                raise BgpParamsError(bgp_as)

        if instance:
            if len(instance) > 31:
                raise InstanceParamsError(instance)

        if group:
            if len(group) > 47:
                raise GroupParamsError(group)

        if peer:
            if len(peer) > 47:
                raise PeerParamsError(peer)

        if peer_connect_intf:
            if peer is None:
                raise BgpMissParamsError(peer)

        if evpn == 'true':
            if address_family is None:
                raise BgpMissParamsError(address_family)
