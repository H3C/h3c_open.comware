"""Manage syslog_global on COM7 devices.
"""


class Syslog(object):

    def __init__(self, device, timestamps, level):
        self.device = device
        self.timestamps = timestamps
        self.level = level

    @staticmethod
    def _get_cmd(**sysLog):

        time = sysLog.get('timestamps')
        leVel = sysLog.get('level')
        commands = []
        cmd_1 = 'info-center '
        #        cmd_4 = 'undo info-center timestamp'
        cmd_2 = 'terminal logging '
        #        cmd_3 = 'undo terminal level'

        if time:
            command_1 = cmd_1 + 'timestamp {0}'.format(time)
            if command_1:
                commands.append(command_1)
        if leVel:
            command_2 = cmd_2 + 'level {0}'.format(leVel)
            if commands:
                commands.append(command_2)
        return commands

    @staticmethod
    def _get_cmd_remove(**sysLog):

        time = sysLog.get('timestamps')
        leVel = sysLog.get('level')

        cmd_1 = 'undo info-center timestamp'
        cmd_2 = 'undo terminal logging'
        commands = []
        if time:
            commands.append(cmd_1)
        if leVel:
            commands.append(cmd_2)
        return commands

    def remove(self, stage=False, **sysLog):

        return self._build_config_absent(state='absent', stage=stage, **sysLog)

    def build(self, stage=False, **sysLog):
        return self._build_config_present(state='present', stage=stage, **sysLog)

    def _build_config_present(self, state, stage=False, **sysLog):

        sysLog['timestamps'] = self.timestamps
        sysLog['level'] = self.level
        c2 = True
        if state == 'present':
            get_cmd = self._get_cmd(**sysLog)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]

    def _build_config_absent(self, state, stage=False, **sysLog):

        sysLog['timestamps'] = self.timestamps
        sysLog['level'] = self.level
        c2 = True
        if state == 'absent':
            get_cmd = self._get_cmd_remove(**sysLog)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]
