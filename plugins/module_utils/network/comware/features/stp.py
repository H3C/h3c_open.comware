"""Manage interfaces on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Stp(object):
    """This class is used to get and handle stp config
    """

    def __init__(self, device, ):
        self.device = device
        self._key_map = {
            'bpdu': 'BPDUProtect',
            'mode': 'Mode',
            'tc': 'TcProtect',
        }
        self._value_map = {
            'Mode': {'0': 'STP',
                     '2': 'RSTP',
                     '3': 'MSTP',
                     '4': 'PVST'},
        }
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

    @staticmethod
    def get_default_config():
        defaults = {'mode': 'MSTP', 'tc': 'true', 'bpdu': 'false'}
        return defaults

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.STP(
                E.Base()
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Base', nc_get_reply)
        if reply_data is None:
            return {}
        return data_elem_to_dict(reply_data, self._key_map, value_map=self._value_map)

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
                        EC.Base(
                            *config_params(params, self._key_map, value_map=self._r_value_map)
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
                        EC.Base(
                            *config_params(defaults, self._key_map, value_map=self._r_value_map)
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

        return False
