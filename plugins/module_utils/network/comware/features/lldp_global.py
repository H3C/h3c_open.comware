"""Manage L2VPN on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, data_elem_to_dict, nc_element_maker, config_element_maker,
    operation_kwarg)


class LLDP(object):
    """Enable/Disable LLDP globally on a Comware 7 switch.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    """

    def __init__(self, device):
        self.device = device

    def get_config(self):
        """Get current L2VPN global configuration state.
        """
        KEYMAP = {
            'enable': 'Enable',
        }

        VALUE_MAP = {
            'Enable': {
                'true': 'enabled',
                'false': 'disabled'
            }
        }

        E = data_element_maker()
        top = E.top(
            E.LLDP(
                E.GlobalStatus()
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        return_lldp = data_elem_to_dict(nc_get_reply, KEYMAP, value_map=VALUE_MAP)

        return return_lldp.get('enable')

    def enable(self, stage=False):
        """Stage or execute a config object to enable L2VPN

        Args:
            stage (bool): whether to stage the commands or execute
                immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='enabled')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def disable(self, stage=False):
        """Stage or execute a config object to disable L2VPN

        Args:
            stage (bool): whether to stage the commands or execute
                immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='disabled')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    @staticmethod
    def _build_config(state):
        """Build config object to configure L2VPN global features

        Args:
            state (str): must be "enabled" or "disabled" and is the desired
                state of the L2VPN global feature

        Returns:
            etree.Element config object to configure L2VPN global features
        """
        value = None
        if state == 'enabled':
            value = 'true'
        elif state == 'disabled':
            value = 'false'

        EN = nc_element_maker()
        EC = config_element_maker()

        config = EN.config(
            EC.top(
                EC.LLDP(
                    EC.GlobalStatus(
                        EC.Enable(value),
                        **operation_kwarg('merge')
                    )
                )
            )
        )

        return config
