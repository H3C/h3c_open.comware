"""Manage telemetry stream on COM7 devices.
"""


class Telemetry(object):

    def __init__(self, device):
        self.device = device

    @staticmethod
    def _get_cmds_present(**telemetry):

        timestamp = telemetry.get('timestamp')
        glo_enable = telemetry.get('glo_enable')
        deviceID = telemetry.get('deviceID')
        commands = []
        cmd_1 = 'telemetry stream timestamp'
        cmd_2 = 'telemetry stream'
        cmd_3 = 'telemetry stream '
        if timestamp == 'enable':
            command_1 = cmd_1 + ' enable'
            if command_1:
                commands.append(command_1)
        if timestamp == 'disable':
            command_1 = 'undo ' + cmd_1 + ' enable'
            if command_1:
                commands.append(command_1)

        if glo_enable == 'enable':
            command_2 = cmd_2 + ' enable'
            if command_2:
                commands.append(command_2)

        if glo_enable == 'disable':
            command_2 = 'undo ' + cmd_2 + ' enable'
            if command_2:
                commands.append(command_2)

        if deviceID:
            command_3 = cmd_3 + 'device-id {0}'.format(deviceID)
            if command_3:
                commands.append(command_3)
        return commands

    @staticmethod
    def _get_cmds_default(**telemetry):

        timestamp = telemetry.get('timestamp')
        glo_enable = telemetry.get('glo_enable')
        deviceID = telemetry.get('deviceID')
        commands = []
        cmd_1 = 'telemetry stream timestamp'
        cmd_2 = 'telemetry stream'
        cmd_3 = 'telemetry stream device-id'

        if timestamp:
            command_1 = 'undo ' + cmd_1 + ' enable'
            if command_1:
                commands.append(command_1)
        if glo_enable:
            command_2 = cmd_2 + ' enable'
            if command_2:
                commands.append(command_2)
        if deviceID:
            command_3 = 'undo ' + cmd_3
            if command_3:
                commands.append(command_3)
        return commands

    def remove(self, stage=False, **telemetry):
        return self._build_config(state='default', stage=stage, **telemetry)

    def build(self, stage=True, **telemetry):

        return self._build_config(state='present', stage=stage, **telemetry)

    def _build_config(self, state, stage=True, **telemetry):
        c1 = True
        c2 = True

        get_cmd = None
        if telemetry.get('timestamp') or telemetry.get('glo_enable'):
            if state == 'present':
                get_cmd = self._get_cmds_present(**telemetry)
            if state == 'default':
                get_cmd = self._get_cmds_default(**telemetry)

            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c1 and c2
        else:
            return [c1, c2]
