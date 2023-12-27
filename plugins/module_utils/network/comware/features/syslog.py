"""Manage syslog information on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Loghost(object):
    """This class is used to get and build syslog host
    configurations on ``COM7`` devices.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
    """

    def __init__(self, device, loghost=None, VRF=None, hostport='514', facility='184'):
        self.device = device
        self.loghost = loghost
        self.VRF = VRF
        self.hostport = hostport
        self.facility = facility

        self.kwargs_key_map = {
            'loghost': 'Address',
            'VRF': 'VRF',
            'hostport': 'Port',
            'facility': 'Facility'
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.Syslog(
                E.LogHosts(
                    E.Host()
                )
            )
        )
        return top

    def get_config(self):
        """
        Returns:
            A dictionary of current configuration parameters.
        """
        top = self.gen_top()
        Loghost_id_ele = find_in_data('Host', top)
        Loghost_id_ele.append(data_element_maker().Address(self.loghost))
        Loghost_id_ele.append(data_element_maker().VRF(self.VRF))
        Loghost_id_ele.append(data_element_maker().Port(self.hostport))
        Loghost_id_ele.append(data_element_maker().Facility(self.facility))

        nc_get_reply = self.device.get(('subtree', top))
        Loghost_config = data_elem_to_dict(nc_get_reply, self.kwargs_key_map)

        return Loghost_config

    def remove(self, stage=False):
        """Stage or execute syslog configuration.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def build(self, stage=False, **kwargs):
        """Stage syslog collectorconfiguration with given parameters.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='present', **kwargs)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **kwargs):
        operation = 'merge'
        if state == 'present':
            operation = 'merge'
            kwargs['loghost'] = self.loghost
            kwargs['VRF'] = self.VRF
            kwargs['hostport'] = self.hostport
            kwargs['facility'] = self.facility

        elif state == 'absent':
            operation = 'delete'

            kwargs['loghost'] = self.loghost
            kwargs['VRF'] = self.VRF

            LOGHOST = kwargs.get('loghost')
            vrf = kwargs.get('VRF')
            if LOGHOST and vrf:
                self.loghost = LOGHOST
                self.VRF = vrf

                kwargs['loghost'] = self.loghost
                kwargs['VRF'] = self.VRF

        EC = nc_element_maker()
        E = config_element_maker()
        config = EC.config(
            E.top(
                E.Syslog(
                    E.LogHosts(
                        E.Host(
                            *config_params(kwargs, self.kwargs_key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def build_time(self, stage=True, **kwargs):

        return self._time_config(state='present', stage=stage, **kwargs)

    def build_time_absent(self, stage=True, **kwargs):
        return self._time_config(state='absent', stage=stage, **kwargs)

    def _time_config(self, state, stage=True, **kwargs):
        c1 = True
        c2 = True
        sourceid = kwargs.get('sourceID')
        if sourceid:
            get_cmd = ""
            if state == 'present':
                get_cmd = self._get_cmds_present(**kwargs)
            if state == 'absent':
                get_cmd = self._get_cmds_absent(**kwargs)

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
    def _get_cmds_present(**kwargs):
        sourceid = kwargs.get('sourceID')
        command = []
        cmd = 'info-center loghost '
        if sourceid:
            command = cmd + 'source {0}'.format(sourceid)
        return command

    @staticmethod
    def _get_cmds_absent(**kwargs):
        sourceid = kwargs.get('sourceID')
        cmd = 'undo info-center loghost source'
        if sourceid:
            return cmd


# syslog source class
class Source(object):
    """This class is used to get and build telemetry stream collector
    configurations on ``COM7`` devices.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
    """

    def __init__(self, device, channelID=None, channelName=None, level=''):

        self.device = device
        self.channelID = channelID
        self.channelName = channelName
        self.level = level

        self.source_key_map = {
            'channelID': 'Destination',
            'channelName': 'MouduleName',
            'level': 'Rule'
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.Syslog(
                E.OutputRules(
                    E.OutputRule()
                )
            )
        )
        return top

    def get_config(self):
        """

        Returns:
            A dictionary of current configuration parameters.

  
        """
        top = self.gen_top()
        source_id_ele = find_in_data('OutputRule', top)
        source_id_ele.append(data_element_maker().Destination(self.channelID))
        source_id_ele.append(data_element_maker().MouduleName(self.channelName))
        source_id_ele.append(data_element_maker().Rule(self.level))

        nc_get_reply = self.device.get(('subtree', top))
        source_config = data_elem_to_dict(nc_get_reply, self.source_key_map)

        return source_config

    def remove(self, stage=False):
        """Stage or execute syslog configuration.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def build(self, stage=False, **kwargs):
        """Stage syslog configuration with given parameters.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='present', **kwargs)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **kwargs):
        operation = 'merge'
        if state == 'present':
            operation = 'merge'
            kwargs['channelID'] = self.channelID
            kwargs['channelName'] = self.channelName
            kwargs['level'] = self.level

        elif state == 'absent':
            operation = 'delete'

            kwargs['channelID'] = self.channelID
            kwargs['channelName'] = self.channelName

            channelid = kwargs.get('channelID')
            channelname = kwargs.get('channelName')

            if channelid and channelname:
                self.channelID = channelid
                self.channelName = channelname

                kwargs['channelID'] = self.channelID
                kwargs['channelName'] = self.channelName

        EC = nc_element_maker()
        E = config_element_maker()
        config = EC.config(
            E.top(
                E.Syslog(
                    E.OutputRules(
                        E.OutputRule(
                            *config_params(kwargs, self.source_key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config
