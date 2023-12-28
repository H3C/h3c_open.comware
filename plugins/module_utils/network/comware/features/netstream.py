"""Manage netstream on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class Netstream(object):

    def __init__(self, device, netstream, rate, timeout, max_entry, vxlan_udp, sampler, mode, sampler_rate,
                 interface_sampler, aggregation, version, BGP, inactive, source_intf, name, interface_enable,
                 host, udp, vpn_name):
        self.device = device
        self.netstream = netstream
        self.rate = rate
        self.sampler = sampler
        self.mode = mode
        self.sampler_rate = sampler_rate
        self.interface_sampler = interface_sampler
        self.timeout = timeout
        self.max_entry = max_entry
        self.vxlan_udp = vxlan_udp
        self.aggregation = aggregation
        self.version = version
        self.BGP = BGP
        self.inactive = inactive
        self.source_intf = source_intf
        self.name = name
        self.interface_enable = interface_enable
        self.host = host
        self.udp = udp
        self.vpn_name = vpn_name

    @staticmethod
    def _get_cmd(**netStream):

        stream = netStream.get('netstream')
        Aggregation = netStream.get('aggregation')
        Sampler = netStream.get('sampler')
        Mode = netStream.get('mode')
        Sampler_rate = netStream.get('sampler_rate')
        Interface_sampler = netStream.get('interface_sampler')
        name = netStream.get('name')
        Version = netStream.get('version')
        bgp = netStream.get('BGP')
        Inactive = netStream.get('inactive')
        Source_intf = netStream.get('source_intf')
        Interface_enable = netStream.get('interface_enable')
        Host = netStream.get('host')
        Udp = netStream.get('udp')
        Vpn_name = netStream.get('vpn_name')
        Rate = netStream.get('rate')
        Timeout = netStream.get('timeout')
        VXLAN_udp = netStream.get('vxlan_udp')
        MAX_entry = netStream.get('max_entry')

        commands = []
        cmd_1 = 'ip netstream'
        cmd_4 = 'undo ip netstream'

        if stream:
            if stream == 'enable':
                commands.append(cmd_1)
            else:
                commands.append(cmd_4)
        if Sampler and Mode and Sampler_rate:
            cmd_15 = 'sampler {0}'.format(Sampler) + ' mode {0}'.format(Mode) + ' packet-interval n-power {0}'.format(
                Sampler_rate)
            commands.append(cmd_15)

        if Rate:
            cmd_6 = 'ip netstream export rate ' + '{0}'.format(Rate)
            commands.append(cmd_6)
        if Timeout:
            cmd_7 = 'ip netstream timeout active ' + '{0}'.format(Timeout)
            commands.append(cmd_7)
        if MAX_entry:
            cmd_8 = 'ip netstream max-entry ' + '{0}'.format(MAX_entry)
            commands.append(cmd_8)
        if VXLAN_udp:
            cmd_9 = 'ip netstream vxlan udp-port ' + '{0}'.format(VXLAN_udp)
            commands.append(cmd_9)

        if Aggregation:
            cmd_5 = 'enable'
            commands.append(cmd_5)
            cmd_2 = 'ip netstream aggregation ' + '{0}'.format(Aggregation)
            commands.insert(-1, cmd_2)
            commands.append('quit')

        if Version and bgp:
            cmd_10 = 'ip netstream export version {0} {1}'.format(Version, bgp)
            commands.append(cmd_10)

        if Inactive:
            cmd_11 = 'ip netstream timeout inactive {0}'.format(Inactive)
            commands.append(cmd_11)

        if Source_intf:
            cmd_12 = 'ip netstream export source interface {0}'.format(Source_intf)
            cmd_13 = 'interface {0}'.format(Source_intf)
            cmd_14 = 'quit'
            commands.append(cmd_13)
            commands.append(cmd_14)
            commands.append(cmd_12)

        if Host and Udp:
            if Vpn_name:
                cmd_5 = 'ip netstream export host ' + '{0}'.format(Host) + ' ' + '{0}'.format(
                    Udp) + ' vpn-instance ' + '{0}'.format(Vpn_name)
            else:
                cmd_5 = 'ip netstream export host ' + '{0}'.format(Host) + ' ' + '{0}'.format(Udp)
            commands.append(cmd_5)

        if Interface_enable:
            if Interface_sampler:
                command_2 = 'ip netstream {0} sampler {1}'.format(Interface_enable, Interface_sampler)
            else:
                command_2 = 'ip netstream {0}'.format(Interface_enable)
            commands.append(command_2)
            command_1 = 'interface {0}'.format(name)
            commands.insert(-1, command_1)
        return commands

    @staticmethod
    def _get_cmd_remove(**netStream):

        stream = netStream.get('netstream')
        aggregation = netStream.get('aggregation')
        name = netStream.get('name')
        Sampler = netStream.get('sampler')
        # Mode = netStream.get('mode')
        # Sampler_rate = netStream.get('sampler_rate')
        Interface_sampler = netStream.get('interface_sampler')
        Version = netStream.get('version')
        # bgp = netStream.get('BGP')
        Inactive = netStream.get('inactive')
        Source_intf = netStream.get('source_intf')
        Interface_enable = netStream.get('interface_enable')
        Host = netStream.get('host')
        #        Udp = netStream.get('udp')
        Vpn_name = netStream.get('vpn_name')
        Rate = netStream.get('rate')
        Timeout = netStream.get('timeout')
        VXLAN_udp = netStream.get('vxlan_udp')
        MAX_entry = netStream.get('max_entry')

        cmd_1 = 'undo ip netstream'
        cmd_2 = 'undo ip netstream aggregation '
        cmd_3 = 'undo ip netstream '
        cmd_6 = 'undo ip netstream export rate'
        cmd_7 = 'undo ip netstream timeout active'
        cmd_8 = 'undo ip netstream max-entry'
        cmd_9 = 'undo ip netstream vxlan udp-port'
        cmd_10 = 'undo ip netstream export source'
        cmd_11 = 'undo ip netstream export version'
        cmd_12 = 'undo ip netstream timeout inactive'
        cmd_13 = 'undo sampler {0}'.format(Sampler)

        commands = []
        if stream:
            commands.append(cmd_1)
        if Sampler:
            commands.append(cmd_13)
        if Rate:
            commands.append(cmd_6)
        if Timeout:
            commands.append(cmd_7)
        if MAX_entry:
            commands.append(cmd_8)
        if VXLAN_udp:
            commands.append(cmd_9)
        if aggregation:
            cmd_5 = cmd_2 + '{0}'.format(aggregation)
            commands.append(cmd_5)
        if Version:
            commands.append(cmd_11)
        if Inactive:
            commands.append(cmd_12)
        if Source_intf:
            commands.append(cmd_10)
        if Interface_enable:
            if Interface_sampler:
                command = cmd_3 + '{0}'.format(Interface_enable) + ' sampler'
            else:
                command = cmd_3 + '{0}'.format(Interface_enable)
            commands.append(command)
            cmd_4 = 'interface {0}'.format(name)
            commands.insert(-1, cmd_4)
        if Host:
            if Vpn_name:
                cmd_5 = 'undo ip netstream export host ' + '{0}'.format(Host) + ' vpn-instance ' + '{0}'.format(
                    Vpn_name)
            else:
                cmd_5 = 'undo ip netstream export host ' + '{0}'.format(Host)
            commands.append(cmd_5)
            if Interface_enable:
                commands.insert(-1, 'quit')
        return commands

    def remove(self, stage=False, **netStream):

        return self._build_config_absent(state='absent', stage=stage, **netStream)

    def build(self, stage=False, **netStream):
        return self._build_config_present(state='present', stage=stage, **netStream)

    def _build_config_present(self, state, stage=False, **netStream):

        netStream['netstream'] = self.netstream
        netStream['aggregation'] = self.aggregation
        netStream['name'] = self.name
        netStream['mode'] = self.mode
        netStream['sampler'] = self.sampler
        netStream['sampler_rate'] = self.sampler_rate
        netStream['interface_sampler'] = self.interface_sampler
        netStream['version'] = self.version
        netStream['BGP'] = self.BGP
        netStream['inactive'] = self.inactive
        netStream['source_intf'] = self.source_intf
        netStream['interface_enable'] = self.interface_enable
        netStream['host'] = self.host
        netStream['udp'] = self.udp
        netStream['vpn_name'] = self.vpn_name
        netStream['rate'] = self.rate
        netStream['timeout'] = self.timeout
        netStream['max_entry'] = self.max_entry
        netStream['vxlan_udp'] = self.vxlan_udp
        c2 = True
        if state == 'present':
            get_cmd = self._get_cmd(**netStream)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]

    def _build_config_absent(self, state, stage=False, **netStream):

        netStream['netstream'] = self.netstream
        netStream['aggregation'] = self.aggregation
        netStream['name'] = self.name
        netStream['mode'] = self.mode
        netStream['sampler'] = self.sampler
        netStream['sampler_rate'] = self.sampler_rate
        netStream['interface_sampler'] = self.interface_sampler
        netStream['version'] = self.version
        netStream['BGP'] = self.BGP
        netStream['inactive'] = self.inactive
        netStream['source_intf'] = self.source_intf
        netStream['interface_enable'] = self.interface_enable
        netStream['host'] = self.host
        netStream['udp'] = self.udp
        netStream['vpn_name'] = self.vpn_name
        netStream['rate'] = self.rate
        netStream['timeout'] = self.timeout
        netStream['max_entry'] = self.max_entry
        netStream['vxlan_udp'] = self.vxlan_udp

        c2 = True
        if state == 'absent':
            get_cmd = self._get_cmd_remove(**netStream)
            if get_cmd:
                if stage:
                    c2 = self.device.stage_config(get_cmd, 'cli_config')
                else:
                    c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]
