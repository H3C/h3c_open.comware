"""Manage switchports on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    config_params)


class Lldp(object):
    """This class is used to get and build lldp interface status
     on ``COM7`` devices.

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
        self.interface_enable = 'unknown'

    @staticmethod
    def get_default():

        return {'interface_enable': 'enabled'}

    def get_config(self):

        key_map = {'interface_enable': 'Enable'}
        value_map = {'Enable': {'true': 'Enabled',
                                'false': 'Disabled'}}

        E = data_element_maker()
        top = E.top(
            E.LLDP(
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

        Interface_value = find_in_data('Enable', nc_get_reply).text

        if Interface_value == 'true':
            self.interface_enable = 'enabled'
        elif Interface_value == 'false':
            self.interface_enable = 'disabled'

        return data_elem_to_dict(reply_data, key_map, value_map=value_map)

    def convert_interface(self, interface_enable, stage=False):
        """Stage or execute the commands to toggle an interface between enabled/disabled.

        Args:
            interface_enable (str): 'enabled' or 'disabled'.
            stage (bool): whether to stage the command or execute immediately

        Note:
            If `link_type` does not equal 'enabled' or 'disabled',
            no commands are staged.

        Returns:
            True if stage=True and successfully staged
            etree.Element XML responses if immediate execution
        """
        if interface_enable == 'enabled':
            Interface_value = 'true'
        elif interface_enable == 'disabled':
            Interface_value = 'false'
        else:
            return

        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.LLDP(
                    EC.Interfaces(
                        EC.Interface(
                            EC.IfIndex(self.interface.iface_index),
                            EC.Enable(Interface_value),
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
        """Stage or execute lldp default configuration.

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        defaults = self.get_default()
        return self.build(stage=stage, **defaults)

    def build(self, stage=False, **params):
        """Stage lldp configuration with given parameters.
        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        interface_enable = params.pop('interface_enable', None)
        if interface_enable == 'enabled':
            if self.interface_enable != 'enabled':
                self.convert_interface(interface_enable, stage)

            key_map = {'interface_enable': 'Enable'}
            config = EN.config(
                EC.top(
                    EC.LLDP(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, key_map)
                            )
                        )
                    )
                )
            )
        elif interface_enable == 'disabled':
            if self.interface_enable != 'disabled':
                self.convert_interface(interface_enable, stage=stage)
            key_map = {'interface_enable': 'Enable'}
            config = EN.config(
                EC.top(
                    EC.LLDP(
                        EC.Interfaces(
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
