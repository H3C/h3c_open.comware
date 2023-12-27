"""Manage ISIS interface on COM7 devices.
"""
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Isis(object):
    """This class is used to get data and configure a specific VLAN.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vlanid (str): VLAN ID

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vlanid (str): VLAN ID

    """

    def __init__(self, device, name=None):
        self.device = device
        if name:
            self.name = name

        # dictionary to XML tag mappings
        self.isis_key_map = {
            'name': 'IfIndex',
            'level': 'LevelType',
            'isisID': 'EnableNameV4',
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.ISIS(
                E.Interfaces(
                    E.Interface()
                )
            )
        )
        return top

    def get_config(self):
        """Gets current configuration for a given VLAN ID

        Args:
            vlanid (str): REQUIRED - VLAN ID

        Returns:
            This returns a dictionary with the following
                k/v pairs:

                :vlanid (str): VLAN ID of the vlan requested
                :name (str): configured name of the vlan
                :descr (str): configured descr of the vlan

            It returns an empty dictionary if the vlan does not exist
        """
        top = self.gen_top()
        isis_id_ele = find_in_data('Interface', top)
        isis_id_ele.append(data_element_maker().IfIndex(self.name))

        nc_get_reply = self.device.get(('subtree', top))
        isis_config = data_elem_to_dict(nc_get_reply, self.isis_key_map)

        return isis_config

    def remove(self, stage=False):
        """Stage or execute XML object for VLAN removal and send to staging

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

    def build(self, stage=False, **isis):
        """Stage or execute XML object for VLAN configuration and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately
            vlan: see Keyword Args

        Keyword Args:
            name (str): OPTIONAL - VLAN name
            descr (str): OPTOINAL - VLAN description

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='present', **isis)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **isis):
        """Build XML object for VLAN configuration

        Args:
            state (str): OPTIONAL must be "present" or "absent"
                DEFAULT is "present"
            vlan: see Keyword Args

            Keyword Args:
                name (str): OPTIONAL - VLAN name
                descr (str): OPTOINAL - VLAN description

        Returns:
            XML object for VLAN configuration
        """
        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'delete'

        EC = nc_element_maker()
        E = config_element_maker()

        isis['name'] = self.name
        config = EC.config(
            E.top(
                E.ISIS(
                    E.Interfaces(
                        E.Interface(
                            *config_params(isis, self.isis_key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config


class ISis(object):
    def __init__(self, device, name, isisID, level, cost, routerid, networkType, silent):
        self.device = device
        self.isisID = isisID
        self.name = name
        self.level = level
        self.cost = cost
        self.routerid = routerid
        self.networkType = networkType
        self.silent = silent

    @staticmethod
    def _get_cmd_present(**isis):
        NetworkType = isis.get('networkType')
        Level = isis.get('level')
        Isis = isis.get('isisID')
        Cost = isis.get('cost')
        Routerid = isis.get('routerid')
        Name = isis.get('name')
        Silent = isis.get('silent')

        commands = []
        if NetworkType or Cost or Routerid or Silent or Level:
            cmd_1 = 'interface {0}'.format(Name)
            commands.append(cmd_1)
            cmd_3 = 'isis enable ' + ' {0}'.format(Isis)
            commands.append(cmd_3)
            if Level:
                cmd_4 = 'isis circuit-level ' + '{0}'.format(Level)
                commands.append(cmd_4)
            if NetworkType:
                comds_1 = 'isis circuit-type p2p'
                commands.append(comds_1)
            if Cost:
                if Routerid:
                    comd_5 = 'isis cost {0}'.format(Cost) + ' {0}'.format(Routerid)
                else:
                    comd_5 = 'isis cost {0}'.format(Cost)
                commands.append(comd_5)

            if Silent:
                if Silent == 'true':
                    comds_3 = 'isis silent'
                else:
                    comds_3 = 'undo isis silent'
                commands.append(comds_3)

        return commands

    @staticmethod
    def _get_cmd_absent(**isis):
        isisid = isis.get('isisID')
        Name = isis.get('name')

        commands = []
        if isisid:
            cmd_1 = 'interface {0}'.format(Name)
            commands.append(cmd_1)
            cmd_2 = 'undo isis enable'
            commands.append(cmd_2)
        return commands

    def build(self, stage=False, **isis):
        return self._build_config(state='present', stage=stage, **isis)

    def remove(self, stage=False, **isis):
        return self._build_config(state='absent', stage=stage, **isis)

    def _build_config(self, state, stage=False, **isis):
        isis['name'] = self.name
        isis['isisID'] = self.isisID
        isis['level'] = self.level
        isis['silent'] = self.silent
        isis['networkType'] = self.networkType
        isis['cost'] = self.cost
        isis['routerid'] = self.routerid

        c2 = True
        get_cmd = None
        if state == 'present':
            get_cmd = self._get_cmd_present(**isis)

        if state == 'absent':
            get_cmd = self._get_cmd_absent(**isis)

        if get_cmd:
            if stage:
                c2 = self.device.stage_config(get_cmd, 'cli_config')
            else:
                c2 = self.device.cli_config(get_cmd)

        if stage:
            return c2
        else:
            return [c2]
