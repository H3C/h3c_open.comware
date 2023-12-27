from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Lacp(object):
    def __init__(self, device, priorityID='32768'):
        self.device = device
        self.priorityID = priorityID

        self.LACP_key_map = {
            'priorityID': 'SystemPriority'

        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.LAGG(
                E.Base()
            )
        )
        return top

    def build_time(self, stage=True, **LACP):

        return self._time_config(state='present', stage=stage, **LACP)

    def build_time_absent(self, stage=True, **LACP):
        return self._time_config(state='default', stage=stage, **LACP)

    # global
    @staticmethod
    def get_default():
        return {'priorityID': '32768'}

    def remove(self, stage=False):

        config = self._build_config(state='default')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def default(self, state, stage=False):
        defaults = self.get_default()
        return self.build(state=state, stage=stage, **defaults)

    def _time_config(self, state, stage=True, **LACP):
        c1 = True
        c2 = True
        get_cmd = None
        sysMAC = LACP.get('sysmac')
        if sysMAC:

            if state == 'present':
                get_cmd = self._get_cmds_present(**LACP)
            if state == 'default':
                get_cmd = self._get_cmds_absent(**LACP)

            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c1 and c2
        else:
            return [c1, c2]

    @staticmethod
    def _get_cmds_absent(**LACP):
        sysMAC = LACP.get('sysmac')

        cmd = 'undo lacp system-mac'
        if sysMAC:
            return cmd

    @staticmethod
    def _get_cmds_present(**LACP):
        sysMAC = LACP.get('sysmac')
        command = []
        cmd = 'lacp system-mac '
        if sysMAC:
            command = cmd + '{0}'.format(sysMAC)
        return command

    def build(self, stage=False, **LACP):

        config = self._build_config(state='present', **LACP)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **LACP):
        operation = None
        if state == 'present':
            operation = 'merge'
            LACP['priorityID'] = self.priorityID

        elif state == 'default':
            operation = 'delete'
            self.priorityID = ''
            LACP['priorityID'] = self.priorityID

        EC = nc_element_maker()
        E = config_element_maker()

        config = EC.config(
            E.top(
                E.LAGG(
                    E.Base(
                        *config_params(LACP, self.LACP_key_map)
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config
