from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Lldp(object):
    def __init__(self, device, module=None, fast_intervalId='1', tx_intervalId='30', multiplierId='4', state=None):
        self.device = device
        self.state = state
        self.module = module

        if fast_intervalId:
            self.fast_intervalId = fast_intervalId
        if tx_intervalId:
            self.tx_intervalId = tx_intervalId
        if multiplierId:
            self.multiplierId = multiplierId

        # netconf xml中的映射关系
        self.LLDP_key_map = {
            'fast_intervalId': 'FastInterval',
            'tx_intervalId': 'TxInterval',
            'multiplierId': 'HoldMult'
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.LLDP(
                E.GlobalStatus()
            )
        )
        return top

    def get_config(self):
        top = self.gen_top()
        LLDP_id_ele = find_in_data('GlobalStatus', top)
        self.fast_intervalId = '1'
        self.tx_intervalId = '30'
        self.multiplierId = '4'

        LLDP_id_ele.append(data_element_maker().FastInterval(self.fast_intervalId))
        LLDP_id_ele.append(data_element_maker().TxInterval(self.tx_intervalId))
        LLDP_id_ele.append(data_element_maker().HoldMult(self.multiplierId))

        nc_get_reply = self.device.get(('subtree', top))
        LLDP_config = data_elem_to_dict(nc_get_reply, self.LLDP_key_map)

        return LLDP_config

    # 恢复时获取默认值
    @staticmethod
    def get_default():
        return {'fast_intervalId': '1', 'tx_intervalId': '30', 'multiplierId': '4'}

    def default(self, state, stage=False):
        defaults = self.get_default()
        return self.build(state=state, stage=stage, **defaults)

    def build(self, state, stage=False, **LLDP):

        config = self._build_config(state, **LLDP)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **LLDP):

        operation = None
        if state == 'present':
            operation = 'merge'
            if 'fast_intervalId' in LLDP:
                self.fast_intervalId = LLDP['fast_intervalId']
            if 'tx_intervalId' in LLDP:
                self.tx_intervalId = LLDP['tx_intervalId']
            if 'multiplierId' in LLDP:
                self.multiplierId = LLDP['multiplierId']
        elif state == 'default':

            operation = 'delete'

            self.fast_intervalId = ''
            self.tx_intervalId = ''
            self.multiplierId = ''

        EC = nc_element_maker()
        E = config_element_maker()

        if hasattr(self, "fast_intervalId"):
            LLDP['fast_intervalId'] = self.fast_intervalId
        if hasattr(self, "tx_intervalId"):
            LLDP['tx_intervalId'] = self.tx_intervalId
        if hasattr(self, "multiplierId"):
            LLDP['multiplierId'] = self.multiplierId
        if state == "default":
            if self.module.params['fast_intervalId'] is None:
                LLDP.pop("fast_intervalId")
            if self.module.params['multiplierId'] is None:
                LLDP.pop("multiplierId")
            if self.module.params['tx_intervalId'] is None:
                LLDP.pop("tx_intervalId")
        config = EC.config(
            E.top(
                E.LLDP(
                    E.GlobalStatus(
                        *config_params(LLDP, self.LLDP_key_map)
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def param_check(self, **LLDP):
        try:
            if hasattr(self, "fast_intervalId"):
                fast_intervalId = self.fast_intervalId
            if hasattr(self, "tx_intervalId"):
                tx_intervalId = self.tx_intervalId
            if hasattr(self, "multiplierId"):
                multiplierId = self.multiplierId
        except ValueError:
            raise LLDPError
