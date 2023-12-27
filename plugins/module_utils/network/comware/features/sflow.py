"""Manage VLANS on COM7 devices.
"""
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    LengthOfStringError, VlanIDError)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Sflow(object):

    def __init__(self, device, collectorID=None):
        self.device = device
        if collectorID:
            self.collectorID = collectorID

        # dictionary to XML tag mappings
        self.sflow_key_map = {
            'collectorID': 'CollectorID',
            'addr': 'IpAddress',
            'vpn': 'VRF',
            'data_size': 'MaxDatagramSize',
            'time_out': 'Timeout',
            'Port': 'Port',
            'descr': 'Description'
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.SFLOW(
                E.sFlowCollector(
                    E.Collector()
                )
            )
        )

        return top

    def get_config(self):

        top = self.gen_top()
        sflow_id_ele = find_in_data('Collector', top)
        sflow_id_ele.append(data_element_maker().CollectorID(self.collectorID))

        nc_get_reply = self.device.get(('subtree', top))
        sflow_config = data_elem_to_dict(nc_get_reply, self.sflow_key_map)

        return sflow_config

    # def remove(self, stage=False):
    #
    #     config = self._build_config(state='absent')
    #     if stage:
    #         return self.device.stage_config(config, 'edit_config')
    #     else:
    #         return self.device.edit_config(config)
    def remove(self, stage=False, **sflow):

        return self._build_config_absent(state='absent', stage=stage, **sflow)

    def _build_config_absent(self, state, stage=False, **sflow):
        sflow['collectorID'] = self.collectorID
        get_cmd = self._get_cmd_remove(**sflow)
        if state == 'absent':
            if get_cmd:
                if stage:
                    return self.device.stage_config(get_cmd, 'cli_config')
                else:
                    return self.device.cli_config(get_cmd)

    @staticmethod
    def _get_cmd_remove(**sflow):
        collectorId = sflow.get('collectorID')
        commands = []
        if collectorId:
            cmd_1 = 'undo sflow collector {0}'.format(collectorId)
            commands.append(cmd_1)
        return commands

    def build(self, stage=False, **sflow):

        config = self._build_config(state='present', **sflow)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state='present', **sflow):
        operation = None
        if state == 'present':
            operation = 'merge'

        EC = nc_element_maker()
        E = config_element_maker()

        sflow['collectorID'] = self.collectorID
        config = EC.config(
            E.top(
                E.SFLOW(
                    E.sFlowCollector(
                        E.Collector(
                            *config_params(sflow, self.sflow_key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def param_check(self, **sflow):

        try:
            collectorID = int(self.collectorID)
        except ValueError:
            raise VlanIDError
        if collectorID < -1 or collectorID > 4094:
            raise VlanIDError

        descr = sflow.get('descr')
        if descr and len(descr) > 254:
            raise LengthOfStringError("'descr'")

        name = sflow.get('name')
        if name and len(name) > 32:
            raise LengthOfStringError("'name'")


class SFlow(object):

    def __init__(self, device, sourceIpv4IP, sourceIpv6IP, agent_ip):
        self.device = device
        # self.state = state

        if agent_ip:
            self.agent_ip = agent_ip
        else:
            self.agent_ip = None
        if sourceIpv4IP:
            self.sourceIpv4IP = sourceIpv4IP
        else:
            self.sourceIpv4IP = None
        if sourceIpv6IP:
            self.sourceIpv6IP = sourceIpv6IP
        else:
            self.sourceIpv6IP = None
        # dictionary to XML tag mappings
        self.sflow_key_map = {
            'agent_ip': 'AgentIpAddress',
            'sourceIpv4IP': 'SourceIpv4Address',
            'sourceIpv6IP': 'SourceIpv6Address'
        }

    def gen_top(self):
        E = data_element_maker()
        top = E.top(
            E.SFLOW(
                E.sFlowConfig()
            )
        )

        return top

    def get_config(self):

        top = self.gen_top()
        sFlow_id_ele = find_in_data('sFlowConfig', top)
        self.sourceIpv6IP = ''
        self.sourceIpv4IP = ''
        self.agent_ip = ''
        sFlow_id_ele.append(data_element_maker().AgentIpAddress(self.agent_ip))
        sFlow_id_ele.append(data_element_maker().SourceIpv4Address(self.sourceIpv4IP))
        sFlow_id_ele.append(data_element_maker().SourceIpv6Address(self.sourceIpv6IP))

        nc_get_reply = self.device.get(('subtree', top))
        sFlow_config = data_elem_to_dict(nc_get_reply, self.sflow_key_map)

        return sFlow_config

    def remove(self, stage=False):

        return self._build_config_absent(state='absent', stage=stage)

    def _build_config_absent(self, state, stage=False):

        if state == 'absent':
            get_cmd = self._get_cmd_remove()

            if get_cmd:
                if stage:
                    return self.device.stage_config(get_cmd, 'cli_config')
                else:
                    return self.device.cli_config(get_cmd)

    def _get_cmd_remove(self):
        commands = []

        if self.agent_ip:
            cmd_1 = 'undo sflow agent ip'
            commands.append(cmd_1)

        if self.sourceIpv4IP:
            cmd_2 = 'undo sflow source ip'
            commands.append(cmd_2)
        if self.sourceIpv6IP:
            cmd_3 = 'undo sflow source ipv6'
            commands.append(cmd_3)

        return commands

    def build(self, stage=False, **sFlow):

        config = self._build_config(state='present', **sFlow)

        if stage:

            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **sFlow):

        operation = None
        if state == 'present':
            operation = 'merge'

        EC = nc_element_maker()
        E = config_element_maker()

        config = EC.config(
            E.top(
                E.SFLOW(
                    E.sFlowConfig(
                        *config_params(sFlow, self.sflow_key_map)
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def debug(self, stage=False):
        return self._build_debug(state='present', stage=stage)

    def _build_debug(self, state, stage=False):
        commands = []
        if state == 'present':
            if self.agent_ip:
                # cmd_1 = 'undo sflow agent ip'
                # commands.append(cmd_1)
                cmd_2 = 'sflow agent ip 1.2.3.4'
                commands.append(cmd_2)

            if commands:
                if stage:
                    return self.device.stage_config(commands, 'cli_config')
                else:
                    return self.device.cli_config(commands)
