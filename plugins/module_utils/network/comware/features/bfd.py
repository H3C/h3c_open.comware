"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Bfd(object):
    """This class is used to get and handle bfd config
    """

    def __init__(self, device, ):
        self.device = device

    def get_config(self):
        dampening_info = {}
        commands = 'dis current-configuration | inc "bfd dampening"'
        rsp = self.device.cli_display(commands)
        by_line = rsp.split('\n')
        if len(by_line) < 3:
            return dampening_info
        # for each in by_line[1:]:
        damp_info = by_line[1]
        if 'dampening' in damp_info:
            dampening = damp_info.split('dampening')[-1].strip()
            dampening_vars = dampening.split(' ')
            damp_max_wait_time = dampening_vars[1]
            damp_init_wait_time = dampening_vars[3]
            secondary = dampening_vars[-1]
            dampening_info = dict(damp_max_wait_time=damp_max_wait_time,
                                  damp_init_wait_time=damp_init_wait_time,
                                  secondary=secondary)
        return dampening_info

    def build(self, stage=False, **kvargs):
        commands = []

        cmds = {
            'dampening': 'bfd dampening maximum {0} initial {1} secondary {2}',
        }

        damp_max_wait_time = kvargs.get('damp_max_wait_time')
        damp_init_wait_time = kvargs.get('damp_init_wait_time')
        secondary = kvargs.get('secondary')

        if damp_max_wait_time:
            commands.append((cmds.get('dampening')).format(damp_max_wait_time,
                                                           damp_init_wait_time,
                                                           secondary))
        if commands:
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def default(self, stage=False):
        commands = ['undo bfd dampening', '\n']

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)
