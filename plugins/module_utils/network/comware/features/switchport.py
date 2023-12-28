"""Manage switchports on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    operation_kwarg, config_params)


class Switchport(object):
    """This class is used to get and build layer 2 interface
    configurations on ``COM7`` devices.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface_name (str): The name of the interface.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface_name (str): The name of the interface.
        interface (comware.features.Interface): The associated
            ``Interface`` configuration object.
    """

    def __init__(self, device, interface_name):
        self.device = device
        self.interface = Interface(device, interface_name)
        self.interface_name = self.interface.interface_name
        self.link_type = 'unknown'

    @staticmethod
    def get_default():
        """Return the default layer 2 settings for a switchport.

        Returns:
            A dictionary of default configuration parameters.

            For example::

                {
                    'pvid': '1',
                    'link_type': 'access'
                }
        """
        return {'pvid': '1', 'link_type': 'access'}

    def get_config(self):
        """Return the current layer 2 settings on the switchport.

        Returns:
            A dictionary of current configuration parameters.

            For example::

                {
                    'pvid': '2',
                    'link_type': 'trunk',
                    'permitted_vlans': '1-5'
                }
        """
        key_map = {'link_type': 'LinkType',
                   'permitted_vlans': 'PermitVlanList',
                   'untaggedvlan': 'UntaggedVlanList',
                   'taggedvlan': 'TaggedVlanList',
                   'pvid': 'PVID'}
        value_map = {'LinkType': {'1': 'access',
                                  '2': 'trunk',
                                  '3': 'hybrid'}}

        E = data_element_maker()
        top = E.top(
            E.VLAN(
                E.Interfaces(
                    E.Interface(
                        E.IfIndex(self.interface.iface_index)
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Interface', nc_get_reply)

        if reply_data is None:
            return {}

        link_type_value = find_in_data('LinkType', nc_get_reply).text

        if link_type_value == '1':
            self.link_type = 'access'
        elif link_type_value == '2':
            self.link_type = 'trunk'
        elif link_type_value == '3':
            self.link_type = 'hybrid'

        return data_elem_to_dict(reply_data, key_map, value_map=value_map)

    def remove_hybrid(self, stage=False):
        """Stage or execute XML object for VLAN removal and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_hybrid_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_trunk(self, stage=False):
        """Stage or execute XML object for VLAN removal and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_trunk_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_access(self, stage=False):
        """Stage or execute XML object for VLAN removal and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_access_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_hybrid_config(self, state, **link_type):
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
            operation = 'remove'
        EN = nc_element_maker()
        EC = config_element_maker()

        key_map = {'untaggedvlan': 'UntaggedVlanList',
                   'taggedvlan': 'TaggedVlanList',
                   'pvid': 'PVID'}
        config = EN.config(
            EC.top(
                EC.VLAN(
                    EC.HybridInterfaces(
                        EC.Interface(
                            EC.IfIndex(self.interface.iface_index),
                            *config_params(link_type, key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def _build_trunk_config(self, state, **link_type):
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
            operation = 'remove'
        EN = nc_element_maker()
        EC = config_element_maker()

        key_map = {'permitted_vlans': 'PermitVlanList',
                   'pvid': 'PVID'}
        config = EN.config(
            EC.top(
                EC.VLAN(
                    EC.TrunkInterfaces(
                        EC.Interface(
                            EC.IfIndex(self.interface.iface_index),
                            *config_params(link_type, key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def _build_access_config(self, state, **link_type):

        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'remove'
        EN = nc_element_maker()
        EC = config_element_maker()

        key_map = {'pvid': 'PVID'}
        config = EN.config(
            EC.top(
                EC.VLAN(
                    EC.AccessInterfaces(
                        EC.Interface(
                            EC.IfIndex(self.interface.iface_index),
                            *config_params(link_type, key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )
        return config

    def convert_interface(self, link_type, stage=False):
        """Stage or execute the commands to toggle an interface between trunk/access.

        Args:
            link_type (str): 'access' or 'trunk'.
            stage (bool): whether to stage the command or execute immediately

        Note:
            If `link_type` does not equal 'access' or 'trunk',
            no commands are staged.

        Returns:
            True if stage=True and successfully staged
            etree.Element XML responses if immediate execution
        """
        if link_type == 'access':
            type_value = '1'
        elif link_type == 'trunk':
            type_value = '2'
        elif link_type == 'hybrid':
            type_value = '3'
        else:
            return

        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.Ifmgr(
                    EC.Interfaces(
                        EC.Interface(
                            EC.IfIndex(self.interface.iface_index),
                            EC.LinkType(type_value),
                        )
                    )
                )
            )
        )

        if stage:
            self.device.stage_config(config, 'edit_config')
        else:
            self.device.edit_config(config)

    def default(self, stage=False):
        """Stage or execute a layer 2 default configuration.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        defaults = self.get_default()
        return self.build(stage=stage, **defaults)

    def build(self, stage=False, **params):
        """Stage a layer 2 configuration with given parameters on switchport.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Keyword Args:
            link_type (str): 'access' or 'trunk'.
            pvid (str): The access VLAN if link_type is 'access',
                the native VLAN if link_type is 'trunk'.
            permitted_vlans (str): A comma and/or hyphen delimited list
                of VLAN numbers. Used when link_type is 'trunk'.
                For example: `1,3-5,7`

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        link_type = params.pop('link_type', '')
        if link_type == 'trunk':
            if self.link_type != 'trunk':
                self.convert_interface(link_type, stage=stage)

            key_map = {'permitted_vlans': 'PermitVlanList',
                       'pvid': 'PVID'}

            config = EN.config(
                EC.top(
                    EC.VLAN(
                        EC.TrunkInterfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, key_map)
                            )
                        )
                    )
                )
            )

        elif link_type == 'hybrid':
            if self.link_type != 'hybrid':
                self.convert_interface(link_type, stage=stage)

            key_map = {'untaggedvlan': 'UntaggedVlanList',
                       'taggedvlan': 'TaggedVlanList',
                       'pvid': 'PVID'}

            config = EN.config(
                EC.top(
                    EC.VLAN(
                        EC.HybridInterfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, key_map)
                            )
                        )
                    )
                )
            )

        elif link_type == 'access':
            if self.link_type != 'access':
                self.convert_interface(link_type, stage=stage)

            key_map = {'pvid': 'PVID'}
            config = EN.config(
                EC.top(
                    EC.VLAN(
                        EC.AccessInterfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, key_map)
                            )
                        )
                    )
                )
            )

        else:
            return

        if params:
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

        return False
