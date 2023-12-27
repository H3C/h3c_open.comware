from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Flowglobal(object):
    def __init__(self, device, module=None, agtime='', state=None):
        self.device = device
        self.state = state
        self.module = module

        if agtime:
            self.agtime = agtime

        self.FLOWGLOBAL_key_map = {
            'agtime': 'AgingTime'
        }

    def gen_top(self):
        E = data_element_maker()
        top = E.top(
            E.TelemetryFlowTrace(
                E.FlowGroupGlobal()
            )
        )
        return top

    # get netconf xml interface
    def get_config(self):
        top = self.gen_top()
        FlowGlobal_id_ele = find_in_data('FlowGroupGlobal', top)
        self.agtime = ''

        FlowGlobal_id_ele.append(data_element_maker().AgingTime(self.agtime))

        nc_get_reply = self.device.get(('subtree', top))
        FLOWGLOBAL_config = data_elem_to_dict(nc_get_reply, self.FLOWGLOBAL_key_map)

        return FLOWGLOBAL_config

    # get default value
    @staticmethod
    def get_default():
        return {'agtime': ''}

    def default(self, state, stage=False):
        defaults = self.get_default()
        return self.build(state=state, stage=stage, **defaults)

    # Make configuration effective
    def build(self, state, stage=False, **FLOWGLOBAL):

        config = self._build_config(state, **FLOWGLOBAL)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    # Configuration according to status
    def _build_config(self, state, **FLOWGLOBAL):

        operation = None
        if state == 'present':
            operation = 'merge'
            if 'agtime' in FLOWGLOBAL:
                self.agtime = FLOWGLOBAL['agtime']

        elif state == 'default':
            operation = 'delete'
            self.agtime = ''

        EC = nc_element_maker()
        E = config_element_maker()

        if hasattr(self, "agtime"):
            FLOWGLOBAL['agtime'] = self.agtime

        if state == "default":
            if self.module.params['agtime'] is None:
                FLOWGLOBAL.pop("agtime")

        config = EC.config(
            E.top(
                E.TelemetryFlowTrace(
                    E.FlowGroupGlobal(
                        *config_params(FLOWGLOBAL, self.FLOWGLOBAL_key_map)
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def param_check(self):
        try:
            if hasattr(self, "agtime"):
                agtime = self.agtime

        except ValueError:
            raise LLDPError
