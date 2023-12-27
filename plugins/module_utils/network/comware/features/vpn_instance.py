"""Manage interfaces on COM7 devices.
"""
import re

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    BgpRelyParamsError, BgpMissParamsError


class Instance(object):
    """This class is used to get and handle stp config
    """

    def __init__(self, device, vpn_instance):
        self.device = device
        self.vpn_instance = vpn_instance

    def get_config(self):
        existing = []
        config = self.device.cli_display('display current-configuration | include vpn-instance')
        instance_config = config.split('\r\n')
        for line in instance_config[1:]:
            if re.search(r'instance', line):
                vsi_name = line.split('instance')[-1]
                existing.append(vsi_name)
        return existing

    def build_vpn(self, stage=False, **kvargs):
        commands = []

        CMDS = {
            'vpn_instance': 'ip vpn-instance {0}',
            'vpn_instance_rd': 'route-distinguisher {0}',
            'address_family': 'address-family {0}',
            'vpn_target': 'vpn-target {0}',
            'vpn_target_mode': 'vpn-target {0} {1}'
        }
        vpn_instance = kvargs.get('vpn_instance')
        vpn_instance_rd = kvargs.get('vpn_instance_rd')
        address_family = kvargs.get('address_family')
        vpn_target = kvargs.get('vpn_target')
        vpn_target_mode = kvargs.get('vpn_target_mode')
        if vpn_instance:
            commands.append((CMDS.get('vpn_instance')).format(vpn_instance))
        if vpn_instance_rd:
            commands.append((CMDS.get('vpn_instance_rd')).format(vpn_instance_rd))
        if address_family:
            commands.append((CMDS.get('address_family')).format(address_family))
        if vpn_target_mode is not None:
            commands.append((CMDS.get('vpn_target_mode')).format(vpn_target, vpn_target_mode))
        else:
            if vpn_target:
                commands.append((CMDS.get('vpn_target')).format(vpn_target))

        if commands:
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def remove_vpn(self, stage=False, **kvargs):
        commands = []
        vpn_instance = kvargs.get('vpn_instance')
        commands.append('undo ip vpn-instance {0}'.format(vpn_instance))
        commands.append('\n')

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    @staticmethod
    def param_check(**params):
        vpn_instance = params.get('vpn_instance')
        address_family = params.get('address_family')
        vpn_target = params.get('vpn_target')
        vpn_target_mode = params.get('vpn_target_mode')

        if vpn_instance:
            if len(vpn_instance) > 31:
                raise BgpRelyParamsError(vpn_instance)
        if address_family:
            if vpn_instance is None:
                raise BgpMissParamsError(vpn_instance)
        if vpn_target_mode:
            if vpn_target is None:
                raise BgpMissParamsError(vpn_target)
        if vpn_target:
            res = re.search(r':', vpn_target)
            if not res:
                raise BgpRelyParamsError(vpn_target)
