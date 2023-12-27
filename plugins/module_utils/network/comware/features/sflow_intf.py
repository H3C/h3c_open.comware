"""Manage sflow interface on COM7 devices.
"""


class Sflow(object):

    def __init__(self, device, intf_name, collector, rate):
        self.device = device
        self.intf_name = intf_name
        self.collector = collector
        self.rate = rate

    @staticmethod
    def _get_cmd(**kwargs):

        index = kwargs.get('intf_name')
        collector = kwargs.get('collector')
        rate = kwargs.get('rate')

        commands = []

        if index:
            cmd_1 = 'interface {0}'.format(index)
            commands.append(cmd_1)
        if collector:
            cmd_2 = 'sflow flow collector {0}'.format(collector)
            commands.append(cmd_2)
        if rate:
            cmd_3 = 'sflow sampling-rate {0}'.format(rate)
            commands.append(cmd_3)

        return commands

    @staticmethod
    def _get_cmd_remove(**kwargs):

        index = kwargs.get('intf_name')
        collector = kwargs.get('collector')
        rate = kwargs.get('rate')

        cmd_1 = 'undo sflow flow collector'
        cmd_2 = 'undo sflow sampling-rate'

        commands = []
        if index:
            cmd_3 = 'interface {0}'.format(index)
            commands.append(cmd_3)
            if collector:
                commands.append(cmd_2)
            if rate:
                commands.append(cmd_1)
        return commands

    def remove(self, stage=False, **kwargs):

        return self._build_config_absent(state='absent', stage=stage, **kwargs)

    def build(self, stage=False, **kwargs):
        return self._build_config_present(state='present', stage=stage, **kwargs)

    def _build_config_present(self, state, stage=False, **kwargs):

        kwargs['intf_name'] = self.intf_name
        kwargs['rate'] = self.rate
        kwargs['collector'] = self.collector

        c2 = True
        if state == 'present':
            get_cmd = self._get_cmd(**kwargs)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]

    def _build_config_absent(self, state, stage=False, **kwargs):

        kwargs['intf_name'] = self.intf_name
        kwargs['rate'] = self.rate
        kwargs['collector'] = self.collector

        c2 = True
        if state == 'absent':
            get_cmd = self._get_cmd_remove(**kwargs)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]
