"""Manage interfaces on COM7 devices.
"""

# from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import reverse_value_map
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    OspfParamsError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Ospf(object):
    """This class is used to get and handle ospf config
    """

    def __init__(self, device, name=None):
        self.device = device
        self.name = name
        self.intf_command = 'interface {0}'.format(name)
        self.interface = Interface(device, name)
        self._key_map = {
            'ospfcost': 'Cost',
            'network_type': 'NetworkType',
        }
        self._value_map = {
            'NetworkType': {'1': 'broadcast',
                            '2': 'nbma',
                            '3': 'p2p',
                            '4': 'p2mp'},
        }
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

    # def get_config(self):
    #     # E = data_element_maker()
    #     # top = E.top(
    #     #     E.OSPF(
    #     #         E.Interfaces(
    #     #             E.Interface(
    #     #                 E.IfIndex(self.interface.iface_index),
    #     #                 E.Cost(),
    #     #                 E.NetworkType(),
    #     #                 E.CurAuthType(),
    #     #             )
    #     #         )
    #     #     )
    #     # )
    #     # nc_get_reply = self.device.get(('subtree', top))
    #     # reply_data = find_in_data('Cost', nc_get_reply)
    #     # print(reply_data,'haha')
    #     # raise IOError
    #     # if reply_data is None:
    #     #     return {}
    #     # return data_elem_to_dict(reply_data, self._key_map, value_map=self._value_map)
    #     defaults = {}
    #     return defaults
    def get_config(self):
        ospf = {}
        # commands = 'dis this | inc ospf'
        commands = 'dis current-configuration interface {0} | inc ospf'.format(self.name)
        res = self.device.cli_display(commands)
        res_by_line = res.split('\n')
        for each in res_by_line[1:]:
            ele = each.split(' ')
            if len(ele) > 2:
                ele_key = ele[2]
                ospf[ele_key] = each

        return ospf

    def build(self, stage=False, **params):
        return self._build_config(state='present', stage=stage, **params)

    def build_area(self, stage=False, **kvargs):
        commands = []

        cmds = {
            'area': 'ospf {0} area {1}',
        }

        ospfname = kvargs.get('ospfname')
        area = kvargs.get('area')

        if area:
            commands.append((cmds.get('area')).format(ospfname, area))

        if commands:
            commands.insert(0, self.intf_command)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def build_auth_simple(self, state, stage=False, **params):
        key_map = {
            'simplepwdtype': 'SimplePwdType',
            'simplepwd': 'SimplePwd',
        }
        value_map = {
            'SimplePwdType': {'1': 'cipher',
                              '2': 'plain'}
        }
        r_key_map = dict(reversed(item) for item in key_map.items())
        r_value_map = reverse_value_map(r_key_map, value_map)
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                EC.SimpleAuth(
                                    *config_params(params, key_map, value_map=r_value_map)
                                )
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

    def build_auth_md5(self, state, stage=False, **params):
        key_map = {
            'keyid': 'KeyId',
            'md5type': 'Md5Type',
            'md5pwdtype': 'PasswordType',
            'md5pwd': 'Password',
        }
        value_map = {
            'Md5Type': {'1': 'md5',
                        '2': 'hwac-md5'},
            'PasswordType': {'1': 'cipher',
                             '2': 'plain'}
        }
        r_key_map = dict(reversed(item) for item in key_map.items())
        r_value_map = reverse_value_map(r_key_map, value_map)
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.IfMd5s(
                            EC.Md5(
                                EC.IfIndex(self.interface.iface_index),
                                *config_params(params, key_map, value_map=r_value_map)
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

    # def default(self, stage=False,**params):
    #     return self._build_config(state='default', stage=stage,**params)
    def default_ospf(self, stage=False):
        existing = self.get_config()
        commands = []
        auth_mode = existing.get('authentication-mode')
        auth_mode_cmd = ''
        if auth_mode:
            auth_mode_lst = auth_mode.split(' ')
            if auth_mode_lst[3] == 'simple':
                auth_mode_cmd = 'undo ospf authentication-mode simple'
            elif auth_mode_lst[3] == 'md5':
                auth_mode_cmd = 'undo ospf authentication-mode md5 {0}'.format(auth_mode_lst[4])
            elif auth_mode_lst[3] == 'hmac-md5':
                auth_mode_cmd = 'undo ospf authentication-mode hmac-md5 {0}'.format(auth_mode_lst[4])
        CMDS = {
            'cost': 'undo ospf cost',
            'network_type': 'undo ospf network-type',
            'authentication-mode': auth_mode_cmd,
        }
        cost = existing.get('cost')
        network_type = existing.get('network-type')

        if cost:
            commands.append(CMDS.get('cost'))
            del existing['cost']
        if network_type:
            commands.append(CMDS.get('network_type'))
            del existing['network-type']
        if auth_mode:
            commands.append(CMDS.get('authentication-mode'))
            del existing['authentication-mode']
        if existing:
            key_lst = []
            for k, v in existing.items():
                key_lst.append(k)
            commands.append('undo ospf {0} area '.format(key_lst[0]))
        if commands:
            commands.insert(0, self.intf_command)
            commands.append('\n')
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def _build_area_config(self, state, stage=False, **params):
        key_map = {
            'ospfname': 'Name',
            'area': 'AreaId'
        }
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
                                EC.IfEnable(
                                    *config_params(params, key_map)
                                )
                            )
                        )
                    )
                )
            )
            if stage:
                return self.device.stage_config(config, 'edit_config')
            else:
                return self.device.edit_config(config)

    def _build_config(self, state, stage=False, **params):
        if state == 'present':
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.OSPF(
                        EC.Interfaces(
                            EC.Interface(
                                EC.IfIndex(self.interface.iface_index),
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

    @staticmethod
    def param_check(**params):
        ospfname = params.get('ospfname')
        ospfcost = params.get('ospfcost')
        # area = params.get('area')
        simplepwdtype = params.get('simplepwdtype')
        simplepwd = params.get('simplepwd')
        keyid = params.get('keyid')
        md5pwdtype = params.get('md5pwdtype')
        md5pwd = params.get('md5pwd')
        if params.get('ospfname'):
            if int(ospfname) < 1 or int(ospfname) > 65535:
                raise OspfParamsError('ospfname error , permitted is 1~65535')
        if ospfcost:
            if int(ospfcost) < 1 or int(ospfcost) > 65535:
                raise OspfParamsError('ospfcost error , permitted is 1~65535')
        # 0-4294967295
        # if area:
        #     if int(area) < 0 or int(area) > 4294967295:
        #         raise OspfParamsError('area')
        if simplepwdtype == 'cipher':
            if simplepwd:
                if len(simplepwd) < 33 or len(simplepwd) > 41:
                    raise OspfParamsError('password not match required')
        elif simplepwdtype == 'plain':
            if simplepwd:
                if len(simplepwd) < 1 or len(simplepwd) > 8:
                    raise OspfParamsError('Simple plain type password length mismatch the range')
        if keyid:
            if int(keyid) < 1 or int(keyid) > 255:
                raise OspfParamsError('keyid error , the range is 1~255')
        if md5pwdtype == 'cipher':
            if md5pwd:
                if len(md5pwd) < 33 or len(md5pwd) > 53:
                    raise OspfParamsError('md5pwd error , mismatch md5 password range')
        elif md5pwdtype == 'plain':
            if md5pwd:
                if len(md5pwd) < 1 or len(md5pwd) > 16:
                    raise OspfParamsError('md5pwd error , mismatch md5 password range')
