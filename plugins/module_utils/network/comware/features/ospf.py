"""Manage interfaces on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    OspfParamsError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Ospf(object):
    """This class is used to get and handle ospf config
    """

    def __init__(self, device, ospfname=None, area=None):
        self.device = device
        if ospfname:
            self.ospfname = ospfname
            self.ospf_config = 'ospf {0}'.format(ospfname)
        if area:
            self.area = area
        self._key_map = {
            'ospfname': 'Name',
            'area': 'AreaId',
            'areatype': 'AreaType',
        }
        self._value_map = {
            'AreaType': {'1': 'Stub',
                         '2': 'NSSA'},
        }
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

    def get_ospf_process(self):
        E = data_element_maker()
        top = E.top(
            E.OSPF(
                E.Instances(
                    E.Instance()
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        ospf_xml = findall_in_data('Name', nc_get_reply)
        ospfs = [ospf.text for ospf in ospf_xml]

        return ospfs

    def get_config(self):
        E = data_element_maker()
        top = E.top(
            E.OSPF(
                E.Instances(
                    E.Instance()
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Instance', nc_get_reply)
        if reply_data is None:
            return {}
        return data_elem_to_dict(reply_data, self._key_map, value_map=self._value_map)

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def build_area(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def build_lsa(self, stage=False, **params):
        return self._build_lsa_config(stage=stage, **params)

    def build_instance(self, stage=False, **params):
        return self._build_instance_config(state='present', stage=stage, **params)

    def build_import(self, stage=False, **params):
        return self._build_import_config(state='present', stage=stage, **params)

    def build_networks(self, stage=False, **params):
        return self._build_networks_config(state='present', stage=stage, **params)

    def default(self, stage=False, **params):
        return self._build_instance_config(state='default', stage=stage, **params)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Areas(
                            EC.Area(
                                *config_params(params, self._key_map, value_map=self._r_value_map)
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

    def _build_instance_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            key_map = {
                'ospfname': 'Name',
                'routerid': 'RouterId',
            }
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Instances(
                            EC.Instance(
                                *config_params(params, key_map)
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
            EN = nc_element_maker()
            EC = config_element_maker()
            operation = 'delete'
            key_map = {
                'ospfname': 'Name',
            }
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Instances(
                            EC.Instance(
                                *config_params(params, key_map)
                            )
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)
        return False

    def _build_lsa_config(self, stage=False, **kvargs):
        commands = []

        CMDS = {
            'lsa_arrival': 'lsa_arrival {0}',
            'lsa_generation_max': 'lsa-generation-interval {0}',
            'lsa_generation_min': 'lsa-generation-interval {0} {1}',
            'lsa_generation_inc': 'lsa-generation-interval {0} {1} {2}',
            'bandwidth': 'bandwidth-reference {0}'
        }
        lsa_generation_max = kvargs.get('lsa_generation_max')
        lsa_generation_min = kvargs.get('lsa_generation_min')
        lsa_generation_inc = kvargs.get('lsa_generation_inc')
        lsa_arrival = kvargs.get('lsa_arrival')
        bandwidth = kvargs.get('bandwidth')

        if lsa_arrival:
            commands.append((CMDS.get('lsa_arrival')).format(lsa_arrival))
        if lsa_generation_max:
            commands.append((CMDS.get('lsa_generation_max')).format(lsa_generation_max))
            if lsa_generation_min:
                commands = [(CMDS.get('lsa_generation_min')).format
                            (lsa_generation_max, lsa_generation_min, )]
                if lsa_generation_inc:
                    commands = [(CMDS.get('lsa_generation_inc')).format
                                (lsa_generation_max, lsa_generation_min, lsa_generation_inc)]
        if bandwidth:
            commands.append((CMDS.get('bandwidth')).format(bandwidth))

        if commands:
            commands.insert(0, self.ospf_config)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def _build_import_config(self, stage=False, **kvargs):
        commands = []

        cmds = {
            'import_route': 'import-route {0}',
        }
        import_route = kvargs.get('import_route')
        if import_route:
            commands.append((cmds.get('import_route')).format(import_route))
        if commands:
            commands.insert(0, self.ospf_config)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def _build_networks_config(self, stage=False, **kvargs):
        commands = []

        cmds = {
            'networkaddr': 'network {0} {1}',
        }
        networkaddr = kvargs.get('networkaddr')
        wildcardmask = kvargs.get('wildcardmask')
        area = kvargs.get('area')
        if networkaddr:
            commands.append((cmds.get('networkaddr')).format(networkaddr, wildcardmask))
        area_view = 'area {0}'.format(area)
        if commands:
            commands.insert(0, area_view)
            commands.insert(0, self.ospf_config)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    @staticmethod
    def param_check(**params):
        ospfname = params.get('ospfname')
        lsa_generation_max = params.get('lsa_generation_max')
        lsa_generation_min = params.get('lsa_generation_min')
        lsa_generation_inc = params.get('lsa_generation_inc')
        lsa_arrival = params.get('lsa_arrival')
        if params.get('ospfname'):
            if int(ospfname) < 1 or int(ospfname) > 65535:
                raise OspfParamsError('ospfname')

        if not params.get('lsa_generation_max'):
            if lsa_generation_min or lsa_generation_inc:
                raise OspfParamsError('lsa_generation_max')

        if not params.get('lsa_generation_min'):
            if lsa_generation_inc:
                raise OspfParamsError('lsa_generation_min')

        if params.get('lsa_generation_max'):
            if int(lsa_generation_max) < 1 or int(lsa_generation_max) > 60:
                raise OspfParamsError('lsa_generation_max')

        if params.get('lsa_generation_min'):
            if int(lsa_generation_min) < 10 or int(lsa_generation_min) > 60000:
                raise OspfParamsError('lsa_generation_min')

        if params.get('lsa_generation_inc'):
            if int(lsa_generation_inc) < 10 or int(lsa_generation_inc) > 60000:
                raise OspfParamsError('lsa_generation_inc')

        if params.get('lsa_arrival'):
            if int(lsa_arrival) < 1 or int(lsa_arrival) > 60000:
                raise OspfParamsError('lsa_arrival')
