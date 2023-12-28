"""Manage interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker, config_params)


class Stp(object):
    """This class is used to get and handle stp config
    """

    def __init__(self, device, interface_name):
        self.device = device
        self.interface = Interface(device, interface_name)
        self.interface_name = self.interface.interface_name
        self._key_map = {
            'edgedport': 'EdgedPort',
            'loop': 'LoopProtect',
            'root': 'RootProtect',
            'tc_restriction': 'TcRestrict',
            'transmit_limit': 'TransmitHoldCount'
        }

    @staticmethod
    def get_default_config():
        defaults = {}
        defaults['edgedport'] = 'false'
        defaults['loop'] = 'false'
        defaults['root'] = 'false'
        defaults['tc_restriction'] = 'false'
        defaults['transmit_limit'] = '10'
        return defaults

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.STP(
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
        return data_elem_to_dict(reply_data, self._key_map)

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def default(self, stage=False):
        return self._build_config(state='default', stage=stage)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.STP(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, self._key_map)
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)
        if state == 'default':
            defaults = self.get_default_config()
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.STP(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(defaults, self._key_map)
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

        return False
