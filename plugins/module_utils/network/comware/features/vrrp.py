"""Manage VRRP groups on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.templates import cli

vrrp_tmpl = r"""Value VRID (\d+)
Value PRIORITY (\d+)
Value PREEMPT (Yes|No)
Value VIP (((\d+.){3}\d+))
Value ADMIN (\w+)


Start
  ^\s+Interface -> TABLE

TABLE
  ^\s+VRID\s+:\s+${VRID}
  ^\s+Admin Status\s+:\s+${ADMIN}
  ^\s+Config Pri\s+:\s+${PRIORITY}
  ^\s+Preempt Mode\s+:\s+${PREEMPT}
  ^\s+Virtual IP\s+:\s+${VIP} -> Record Start
"""


class VRRP(object):
    """This class is used to collect data or configure a VRRP group on a
        given interface.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface (str): name of the Layer 3 interface
        vrid (str): virtual router ID (group number)


    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface (str): name of the Layer 3 interface
        vrid (str): virtual router ID (group number)


    """

    def __init__(self, device, interface, vrid):
        self.device = device
        self.interface = interface
        self.vrid = vrid

        # contains response from using CLI method
        self._existing_all = None

        # interface command used when sending CLI commands
        self.intf_command = 'interface {0}'.format(interface)

    def get_vrrp_groups(self):
        """Get list of VRIDs for a given Layer 3 interface

        Returns:
            This returns a list of VRIDs configured on a given interface.

        """
        commands = 'display vrrp interface {0} verbose'.format(self.interface)
        rsp = self.device.cli_display(commands)
        self._existing_all = cli.get_structured_data(vrrp_tmpl, rsp)
        vrids = [each.get('vrid') for each in self._existing_all
                 if each.get('vrid')]
        return vrids

    def get_auth_type(self):
        """Get auth type for a given VRID on a given interface

        Returns:
           This returns a dictionary with the following k/v pairs:
               :auth_mode (str): "simple" or "md5"
               :key_type (str): "cipher"
               :key (str): it will be a cipher

           It will return an empty dictionary if it VRID
           does not exist.

        """
        auth = {}
        commands = 'display current-configuration interface' \
                   + ' {0} | inc "vrid {1} auth"'.format(self.interface,
                                                         self.vrid)
        rsp = self.device.cli_display(commands)
        by_line = rsp.split('\n')
        for each in by_line[1:]:
            if 'authentication-mode' in each:
                auth = each.split('authentication-mode')[-1].strip()
                auth_vars = auth.split(' ')
                if len(auth_vars) == 3:
                    auth_mode = auth_vars[0]
                    key_type = auth_vars[1]
                    key = auth_vars[2]
                    auth = dict(auth_mode=auth_mode, key_type=key_type,
                                key=key)
        return auth

    def get_track_info(self):
        """Get auth type for a given VRID on a given interface

        Returns:
           This returns a dictionary with the following k/v pairs:
               :auth_mode (str): "simple" or "md5"
               :key_type (str): "cipher"
               :key (str): it will be a cipher

           It will return an empty dictionary if it VRID
           does not exist.

        """
        track = {}
        commands = 'display current-configuration interface' \
                   + ' {0} | inc "vrid {1} track"'.format(self.interface,
                                                          self.vrid)
        rsp = self.device.cli_display(commands)
        by_line = rsp.split('\n')
        for each in by_line[1:]:
            if 'track' in each:
                track = each.split('track')[-1].strip()
                track_vars = track.split(' ')
                if len(track_vars) == 2:
                    track = track_vars[0]
                    switch = track_vars[1]
                    track = dict(track=track, switch=switch, )
        return track

    @staticmethod
    def _apply_value_maps(existing):
        """Manipulating value for preempt
        """

        if existing.get('preempt'):
            existing['preempt'] = existing.get('preempt').lower()

        return existing

    def remove(self, stage=False):
        """Stage or execute commands to remove VRRP group.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            CLI response string if immediate execution
        """
        commands = []
        commands.append(self.intf_command)
        commands.append('undo vrrp vrid {0}'.format(self.vrid))
        commands.append('\n')

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def shutdown(self, stage=False):
        """Stage or execute commands to shutdown VRRP group.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            CLI response string if immediate execution
        """
        commands = []
        commands.append(self.intf_command)
        commands.append('vrrp vrid {0} shutdown'.format(self.vrid))
        commands.append('\n')

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def undoshutdown(self, stage=False):
        """Stage or execute commands to undo shutdown of VRRP group.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            CLI response string if immediate execution
        """
        commands = []
        commands.append(self.intf_command)
        commands.append('undo vrrp vrid {0} shutdown'.format(self.vrid))
        commands.append('\n')

        if stage:
            return self.device.stage_config(commands, 'cli_config')
        else:
            return self.device.cli_config(commands)

    def get_config(self):
        """Get the config of a given vrid on a given interface

        Returns:
            This returns a dictionary with the following k/v pairs:
               :auth_mode (str): "simple" or "md5"
               :key_type (str): "cipher"
               :key (str): it will be a cipher
               :priority (str): VRRP priority
               :preempt (str): "true" or "false" (STRING)
               :vip (str): virtual IP address

        """

        self.get_vrrp_groups()
        config = [each for each in self._existing_all
                  if each.get('vrid') == self.vrid]
        existing = None
        if len(config) == 0:
            existing = {}
        elif len(config) == 1:
            existing = config[0]
            auth = self.get_auth_type()
            existing.update(auth)
            track = self.get_track_info()
            existing.update(track)
            existing = self._apply_value_maps(existing)
        return existing

    def build(self, stage=False, **kvargs):
        """Execute or stage XML VRRP configuration and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately
            kvargs: see Keyword Args

        Note:
            If auth is being configured, all three auth Keyword
            Args are required.

        Keyword Args:
            vip (str): REQUIRED - virtual IP address
            auth_mode (str): OPTIONAL - "simple" or "md5"
            key_type (str): OPTIONAL - "cipher" or "plain"
            key (str): OPTIONAL - text string if ``key_type`` is "plain" or
                cipher if ``key_type`` is "cipher"
            priority (str): OPTIONAL - VRRP priority
            preempt (str): OPTIONAL - "yes" or "no" (STRING)

        Returns:
            True if stage=True and successfully staged
            CLI response if immediate execution
        """
        commands = []

        cmds = {
            'priority': 'vrrp vrid {0} priority {1}',
            'preempt': 'vrrp vrid {0} preempt-mode',
            'delay': 'vrrp vrid {0} preempt-mode delay {1}',
            'vip': 'vrrp vrid {0} virtual-ip {1}',
            'auth': 'vrrp vrid {0} authentication-mode {1} {2} {3}',
            'track': 'vrrp vrid {0} track {1} {2}',
        }

        vip = kvargs.get('vip')
        prio = kvargs.get('priority')
        preempt = kvargs.get('preempt')
        delay = kvargs.get('delay')
        auth_mode = kvargs.get('auth_mode')
        key_type = kvargs.get('key_type')
        key = kvargs.get('key')
        track = kvargs.get('track')
        switch = kvargs.get('switch')

        if vip:
            commands.append((cmds.get('vip')).format(self.vrid, vip))
        if prio:
            commands.append((cmds.get('priority')).format(self.vrid, prio))
        if preempt == 'yes':
            commands.append(cmds.get('preempt').format(self.vrid))
        elif preempt == 'no':
            commands.append('undo ' + cmds.get('preempt').format(self.vrid))
        if delay:
            commands.append(cmds.get('delay').format(self.vrid, delay))
        if auth_mode:
            commands.append((cmds.get('auth')).format(self.vrid, auth_mode,
                                                      key_type, key))
        if track:
            commands.append((cmds.get('track')).format(self.vrid, track, switch))

        if commands:
            commands.insert(0, self.intf_command)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)
