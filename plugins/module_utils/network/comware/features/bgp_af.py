"""Manage interfaces on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    BgpAfParamsError, BgpAfConfigError)
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
        commands.append('undo bgp {0} instance {1}'.format(bgp_as,
                                                           bgp_instance))
        commands.append('\n')
        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def build_bgp_af(self, stage=False, **kvargs):
        commands = []
        CMDS = {
            'address_familys': 'address-family {0}',
            'local_pref': 'default local-preference {0}',
            'policy_target': 'policy vpn-target',
            'frr_policy': 'fast-reroute route-policy frr-policy',
            'route_select_delay': 'route-select delay {0}',
            'allow_invalid_as': 'bestroute origin-as-validation allow-invalid',
        }
        bgp_as = kvargs.get('bgp_as')
        bgp_instance = kvargs.get('bgp_instance')
        address_familys = kvargs.get('address_familys')
        local_pref = kvargs.get('local_pref')
        policy_target = kvargs.get('policy_target')
        frr_policy = kvargs.get('frr_policy')
        route_select_delay = kvargs.get('route_select_delay')
        allow_invalid_as = kvargs.get('allow_invalid_as')
        if address_familys:
            commands.append(CMDS.get('address_familys').format(address_familys))
        if local_pref:
            commands.append(CMDS.get('local_pref').format(local_pref))
        if policy_target:
            commands.append(CMDS.get('policy_target').format(policy_target))
        if frr_policy:
            commands.append(CMDS.get('frr_policy').format(frr_policy))
        if route_select_delay:
            commands.append(CMDS.get('route_select_delay').format(route_select_delay))
        if allow_invalid_as:
            commands.append(CMDS.get('allow_invalid_as'))

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

    @staticmethod
    def param_check(**params):
        """Checks given parameters
        """
        local_pref = params.get('local_pref')
        route_select_delay = params.get('route_select_delay')
        # 0 - 4294967295
        if local_pref:
            if int(local_pref) < 0 or int(local_pref) > 4294967295:
                raise BgpAfParamsError(local_pref)
        if route_select_delay:
            if int(route_select_delay) < 0 or int(route_select_delay) > 600:
                raise BgpAfParamsError(route_select_delay)

        if params.get('address_familys') == 'vpnv4' or params.get('address_familys') == 'vpnv6':
            if params.get('frr_policy'):
                raise BgpAfConfigError('frr_policy')

        if params.get('address_familys') == 'vpnv4' or params.get('address_familys') == 'vpnv6':
            if params.get('local_pref'):
                raise BgpAfConfigError('local_pref')

        if params.get('address_familys') == 'vpnv4' or params.get('address_familys') == 'vpnv6':
            if params.get('policy_target'):
                raise BgpAfConfigError('policy_target')

        if params.get('address_familys') == 'vpnv4' or params.get('address_familys') == 'vpnv6':
            if params.get('allow_invalid_as'):
                raise BgpAfConfigError('allow_invalid_as')
