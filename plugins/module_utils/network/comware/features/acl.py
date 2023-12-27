"""Manage ACL on COM7 devices.
author: liudongxue
"""

# from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import reverse_value_map
# from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    InterfaceTypeError, InterfaceAbsentError)
# from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vlan import Vlan
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface


class Acl(object):
    """This class is used to build acl configurations on ``COM7`` devices.

    """

    def __init__(self, device, acl_id, interface_name, rule_id, scripaddr):
        # used to map key values from our dictionary model
        # to expected XML tags and vice versa
        self._key_map = {
            'appdirec': 'AppDirection'
        }
        # used to map value values from our dictionary model
        # to expected XML tags and vice versa
        self._value_map = {
            'AppDirection': {'1': 'inbound',
                             '2': 'outbound'}
        }
        self._key_map_rule = {
            'groupcg': 'GroupCategory'
        }

        # used to map value values from our dictionary model
        # to expected XML tags and vice versa
        self._value_map_rule = {
            'GroupCategory': {'1': 'basic',
                              '2': 'advanced'}
        }
        # xml tags
        self._iface_row_name = 'Interface'
        self._iface_index_name = 'IfIndex'
        self._group_id = 'GroupID'
        self._rule_id = 'RuleID'
        self._prototype = 'ProtocolType'
        self._src_any = 'SrcAny'
        self._src_ip_addr = 'SrcIPv4Addr'
        self._src_ip_wild_card = 'SrcIPv4Wildcard'
        self._app_obj_type = 'AppObjType'
        self._app_obj_index = 'AppObjIndex'
        self._app_acl_group = 'AppAclGroup'
        self._action = 'Action'
        self._app_acl_type = 'AppAclType'
        self._group_type = 'GroupType'
        self._group_index = 'GroupIndex'
        self.protocltype = '256'
        self.scripwaddr = '0.0.0.0'
        self.srcany = 'false'
        self.appobjtype = '1'
        self.appacltype = '1'
        self.grouptype = '1'
        # usd in conjunction with key map and value map above
        self._r_key_map = dict(reversed(item) for item in self._key_map.items())
        self._r_value_map = reverse_value_map(self._r_key_map, self._value_map)

        self._r_key_map_rule = dict(reversed(item) for item in self._key_map_rule.items())
        self._r_value_map_rule = reverse_value_map(self._r_key_map_rule, self._value_map_rule)
        # connect to the device and get more information

        self.ruleid = rule_id
        interface = Interface(device, interface_name)
        self.groupid = acl_id
        self.scripaddr = scripaddr
        self.device = device
        self.interface_name, self.iface_type, subiface_num = interface._iface_type(interface_name)
        # The interface index is needed for most interface NETCONF requests
        self.iface_index = interface._get_iface_index()
        self.iface_exists = True if self.iface_index != 1 else False

    def create_acl(self, stage=False, **params):
        params[self._group_type] = self.grouptype
        params[self._group_index] = self.groupid
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.ACL(
                    EC.NamedGroups(
                        EC.Group(
                            *config_params(params, self._key_map_rule, value_map=self._r_value_map_rule)
                        )
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove_acl(self, stage=False, **params):
        operation = 'delete'
        params[self._group_type] = self.grouptype
        params[self._group_index] = self.groupid
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.ACL(
                    EC.NamedGroups(
                        EC.Group(
                            *config_params(params, self._key_map_rule, value_map=self._r_value_map_rule)
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def create_rule(self, stage=False, action='deny'):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = None
        if action == 'deny':
            config = EN.config(
                EC.top(
                    EC.ACL(
                        EC.IPv4AdvanceRules(
                            EC.Rule(
                                EC.GroupID(self.groupid),
                                EC.RuleID(self.ruleid),
                                EC.Action('1'),
                                EC.ProtocolType(self.protocltype),
                                EC.SrcAny(self.srcany),
                                EC.SrcIPv4(
                                    EC.SrcIPv4Addr(self.scripaddr),
                                    EC.SrcIPv4Wildcard(self.scripwaddr)
                                )
                            )
                        )
                    )
                )
            )

        if action == 'permit':
            config = EN.config(
                EC.top(
                    EC.ACL(
                        EC.IPv4AdvanceRules(
                            EC.Rule(
                                EC.GroupID(self.groupid),
                                EC.RuleID(self.ruleid),
                                EC.Action('2'),
                                EC.ProtocolType(self.protocltype),
                                EC.SrcAny(self.srcany),
                                EC.SrcIPv4(
                                    EC.SrcIPv4Addr(self.scripaddr),
                                    EC.SrcIPv4Wildcard(self.scripwaddr)
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

    def remove_rule(self, stage=False):
        EN = nc_element_maker()
        EC = config_element_maker()
        operation = 'delete'
        config = EN.config(
            EC.top(
                EC.ACL(
                    EC.IPv4AdvanceRules(
                        EC.Rule(
                            EC.GroupID(self.groupid),
                            EC.RuleID(self.ruleid)
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def create_packet_filter(self, stage=False, **params):
        config = None
        if self.iface_exists:
            params[self._app_obj_type] = self.appobjtype
            params[self._app_obj_index] = self.iface_index
            params[self._app_acl_group] = self.groupid
            params[self._app_acl_type] = self.appacltype
            EN = nc_element_maker()
            EC = config_element_maker()
            config = EN.config(
                EC.top(
                    EC.ACL(
                        EC.PfilterApply(
                            EC.Pfilter(
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
        if not self.iface_exists:
            if self.iface_type in {'FortyGigE', 'GigabitEthernet',
                                   'TwentyGigE', 'Twenty-FiveGigE', 'Ten-GigabitEthernet',
                                   'HundredGigE'}:
                raise InterfaceAbsentError(self.interface_name)

    def remove_packet_filter(self, stage=False, **params):
        params[self._app_obj_type] = self.appobjtype
        params[self._app_obj_index] = self.iface_index
        params[self._app_acl_group] = self.groupid
        params[self._app_acl_type] = self.appacltype
        operation = 'delete'
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.ACL(
                    EC.PfilterApply(
                        EC.Pfilter(
                            *config_params(params, self._key_map, value_map=self._r_value_map)
                        ),
                        **operation_kwarg(operation)
                    )
                )
            )
        )

        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def param_check(self, **params):
        """Checks given parameters against the interface for various errors.

        """
        if not self.iface_type:
            raise InterfaceTypeError(
                self.interface_name, list(self._iface_types))

        if not self.iface_exists:
            if self.iface_type in {'FortyGigE', 'GigabitEthernet',
                                   'TwentyGigE', 'Twenty-FiveGigE', 'Ten-GigabitEthernet',
                                   'HundredGigE'}:
                raise InterfaceAbsentError(self.interface_name)
