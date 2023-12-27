"""Manage interfaces on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Bgp(object):
    """This class is used to get and handle stp config
    """

    def __init__(self, device, ):
        self.device = device
        self._key_map = {
            'bgp_as': 'ASNumber',
            'bgp_instance': 'Name',
        }

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.BGP(
                E.Instances(
                    E.Instance()
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Instance', nc_get_reply)
        if reply_data is None:
            return {}
        return data_elem_to_dict(reply_data, self._key_map)

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.BGP(
                        EC.Instances(
                            EC.Instance(
                                *config_params(params, self._key_map)
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

    def remove_bgp(self, stage=False, **kvargs):
        commands = []
        bgp_as = kvargs.get('bgp_as')
        bgp_instance = kvargs.get('bgp_instance')
        if bgp_instance:
            commands.append('undo bgp {0} instance {1}'.format(bgp_as,
                                                               bgp_instance))
        else:
            commands.append('undo bgp {0}'.format(bgp_as))
        commands.append('\n')
        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def build_bgp_global(self, stage=False, **kvargs):
        commands = []
        CMDS = {
            'router_id': 'router-id {0}',
            'advertise_rib_active': 'advertise-rib-active',
            'timer_connect_retry': 'timer connect-retry {0}',
            'timer_keepalive_hold': 'timer keepalive {0} hold {1}',
            'compare_as_med': 'compare-different-as-med',
            'peer': 'peer {0} as-number {1}',
            'peer_ignore': 'peer {0} ignore',
            'peer_connect_intf': 'peer {0} connect-interface {1}',
            'address_family': 'address-family {0}',
            'evpn': 'address-family {0} {1}',
            'peer_state': 'peer {0} enable',
        }
        bgp_as = kvargs.get('bgp_as')
        bgp_instance = kvargs.get('bgp_instance')
        router_id = kvargs.get('router_id')
        advertise_rib_active = kvargs.get('advertise_rib_active')
        timer_connect_retry = kvargs.get('timer_connect_retry')
        timer_keepalive = kvargs.get('timer_keepalive')
        timer_hold = kvargs.get('timer_hold')
        compare_as_med = kvargs.get('compare_as_med')
        peer_ip = kvargs.get('peer_ip')
        peer_as_num = kvargs.get('peer_as_num')
        peer_ignore = kvargs.get('peer_ignore')
        peer_connect_intf = kvargs.get('peer_connect_intf')
        address_family = kvargs.get('address_family')
        evpn = kvargs.get('evpn')
        peer_state = kvargs.get('peer_state')
        if router_id:
            commands.append((CMDS.get('router_id')).format(router_id))
        if advertise_rib_active == 'true':
            commands.append(CMDS.get('advertise_rib_active'))
        if timer_connect_retry:
            commands.append(CMDS.get('timer_connect_retry').format(timer_connect_retry))
        if timer_hold:
            commands.append(CMDS.get('timer_keepalive_hold').format(timer_keepalive, timer_hold))
        if compare_as_med == 'true':
            commands.append(CMDS.get('compare_as_med'))
        if peer_ip and peer_as_num:
            commands.append(CMDS.get('peer').format(peer_ip, peer_as_num))
        if peer_ignore == 'true' and peer_ip:
            commands.append(CMDS.get('peer_ignore').format(peer_ip))
        if peer_connect_intf:
            commands.append(CMDS.get('peer_connect_intf').format(peer_ip, peer_connect_intf))
        if address_family and evpn == 'false':
            commands.append(CMDS.get('address_family').format(address_family))
        if evpn == 'true':
            commands.append(CMDS.get('evpn').format(address_family, 'evpn'))
        if peer_state == 'true':
            commands.append(CMDS.get('peer_state').format(peer_ip))
        if bgp_instance:
            instance_view = 'bgp {0} instance {1}'.format(bgp_as, bgp_instance)
            commands.insert(0, instance_view)
        else:
            as_view = 'bgp {0}'.format(bgp_as)
            commands.insert(0, as_view)
        commands.append('\n')
        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)
