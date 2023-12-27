"""Manage dldp on COM7 devices.
"""


class Dldp(object):

    def __init__(self, device, global_enable, auth_mode, timeout, port_shutdown, pwd_mode, init_delay,
                 pwd, name, interface_enable, shutdown_mode):
        self.device = device
        self.global_enable = global_enable
        self.auth_mode = auth_mode
        self.timeout = timeout
        self.pwd_mode = pwd_mode
        self.init_delay = init_delay
        self.pwd = pwd
        self.name = name
        self.interface_enable = interface_enable
        self.shutdown_mode = shutdown_mode
        self.port_shutdown = port_shutdown

    @staticmethod
    def _get_cmd(**DLDP):

        global_enable = DLDP.get('global_enable')
        auth_mode = DLDP.get('auth_mode')
        name = DLDP.get('name')
        interface_enable = DLDP.get('interface_enable')
        pwd_mode = DLDP.get('pwd_mode')
        init_delay = DLDP.get('init_delay')
        pwd = DLDP.get('pwd')
        shutdown_mode = DLDP.get('shutdown_mode')
        port_shutdown = DLDP.get('port_shutdown')
        timeout = DLDP.get('timeout')

        commands = []
        cmd_1 = 'dldp global enable'
        cmd_2 = 'dldp authentication-mode '
        cmd_3 = 'dldp authentication-password '
        cmd_4 = 'dldp enable'
        cmd_5 = 'dldp unidirectional-shutdown '
        cmd_6 = 'dldp port unidirectional-shutdown '
        cmd_7 = 'undo dldp global enable'
        cmd_12 = 'dldp interval '
        cmd_16 = 'undo dldp enable'
        if global_enable:
            if global_enable == 'enable':
                commands.append(cmd_1)
            else:
                commands.append(cmd_7)
        if auth_mode:
            cmd_8 = cmd_2 + '{0}'.format(auth_mode)
            commands.append(cmd_8)
        if pwd:
            cmd_9 = cmd_3 + '{0}'.format(pwd_mode) + ' {0}'.format(pwd)
            commands.append(cmd_9)
        if shutdown_mode:
            cmd_10 = cmd_5 + '{0}'.format(shutdown_mode)
            commands.append(cmd_10)
        if timeout:
            cmd_11 = cmd_12 + '{0}'.format(timeout)
            commands.append(cmd_11)
        if name:
            cmd_13 = 'interface ' + '{0}'.format(name)
            commands.append(cmd_13)
            if interface_enable and not init_delay:
                if interface_enable == 'enable':
                    commands.append(cmd_4)
                else:
                    commands.append(cmd_16)
            if interface_enable and init_delay:
                cmd_14 = cmd_4 + ' initial-unidirectional-delay ' + '{0}'.format(init_delay)
                commands.append(cmd_14)
            if port_shutdown:
                cmd_15 = cmd_6 + '{0}'.format(port_shutdown)
                commands.append(cmd_15)

        return commands

    @staticmethod
    def _get_cmd_remove(**DLDP):

        global_enable = DLDP.get('global_enable')
        auth_mode = DLDP.get('auth_mode')
        name = DLDP.get('name')
        interface_enable = DLDP.get('interface_enable')
        pwd_mode = DLDP.get('pwd_mode')
        init_delay = DLDP.get('init_delay')
        #        Pwd = DLDP.get('pwd')
        shutdown_mode = DLDP.get('shutdown_mode')
        port_shutdown = DLDP.get('port_shutdown')
        timeout = DLDP.get('timeout')

        cmd_1 = 'undo dldp global enable'
        cmd_2 = 'undo dldp authentication-mode'
        cmd_3 = 'undo dldp interval'
        cmd_4 = 'undo dldp unidirectional-shutdown'
        cmd_6 = 'undo dldp enable'
        cmd_7 = 'undo dldp port unidirectional-shutdown'
        cmd_8 = 'undo dldp authentication-password'
        commands = []
        if global_enable:
            commands.append(cmd_1)
        if auth_mode:
            commands.append(cmd_2)
        if pwd_mode:
            commands.append(cmd_8)
        if timeout:
            commands.append(cmd_3)
        if shutdown_mode:
            commands.append(cmd_4)
        if name:
            cmd_5 = 'interface ' + '{0}'.format(name)
            commands.append(cmd_5)
            if interface_enable:
                commands.append(cmd_6)
            if port_shutdown:
                commands.append(cmd_7)

        return commands

    def remove(self, stage=False, **DLDP):

        return self._build_config_absent(state='absent', stage=stage, **DLDP)

    def build(self, stage=False, **DLDP):
        return self._build_config_present(state='present', stage=stage, **DLDP)

    def _build_config_present(self, state, stage=False, **DLDP):

        DLDP['global_enable'] = self.global_enable
        DLDP['auth_mode'] = self.auth_mode
        DLDP['pwd_mode'] = self.pwd_mode
        DLDP['interface_enable'] = self.interface_enable
        DLDP['pwd'] = self.pwd
        DLDP['timeout'] = self.timeout
        DLDP['name'] = self.name
        DLDP['init_delay'] = self.init_delay
        DLDP['shutdown_mode'] = self.shutdown_mode
        DLDP['port_shutdown'] = self.port_shutdown

        c2 = True
        if state == 'present':
            get_cmd = self._get_cmd(**DLDP)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]

    def _build_config_absent(self, state, stage=False, **DLDP):

        DLDP['global_enable'] = self.global_enable
        DLDP['auth_mode'] = self.auth_mode
        DLDP['pwd_mode'] = self.pwd_mode
        DLDP['interface_enable'] = self.interface_enable
        DLDP['pwd'] = self.pwd
        DLDP['timeout'] = self.timeout
        DLDP['name'] = self.name
        DLDP['init_delay'] = self.init_delay
        DLDP['shutdown_mode'] = self.shutdown_mode
        DLDP['port_shutdown'] = self.port_shutdown

        c2 = True
        if state == 'absent':
            get_cmd = self._get_cmd_remove(**DLDP)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]
