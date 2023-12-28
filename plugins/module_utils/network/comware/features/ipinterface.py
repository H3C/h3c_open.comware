"""Manage layer 3 interfaces on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ipaddress

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import IpIfaceMissingData
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    config_params, operation_kwarg)

V4 = 'v4'
V6 = 'v6'


class IpInterface(object):
    """This class is used to get and build layer 3
    interface configurations on ``COM7`` devices.

    Args:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
        interface_name (str): The name of the interface.
        version (str): V4 for IPv4, V6 for IPv6

    Attributes:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
        interface_name (str): The name of the interface.
        version (str): V4 for IPv4, V6 for IPv6
        interface (comware.features.Interface): The associated
            ``Interface`` configuration object.
        is_routed (bool): ``True`` if the interface is in layer 3
            mode, ``False`` otherwise.
    """
    def __init__(self, device, interface_name, version=V4):
        self.device = device
        self.interface = Interface(device, interface_name)
        self.interface_name = self.interface.interface_name
        self.is_routed = self.interface.is_routed
        self.version = version

    def gen_ipv4_top(self):
        E = data_element_maker()
        top = E.top(
            E.IPV4ADDRESS(
                E.Ipv4Addresses(
                    E.Ipv4Address(
                        E.IfIndex(self.interface.iface_index),
                        E.Ipv4Address(),
                        E.Ipv4Mask(),
                    )
                )
            )
        )

        return top

    def gen_ipv6_top(self):
        E = data_element_maker()
        top = E.top(
            E.IPV6ADDRESS(
                E.Ipv6Addresses(
                    E.AddressEntry(
                        E.IfIndex(self.interface.iface_index),
                        E.Ipv6Address(),
                        E.Ipv6PrefixLength(),
                    )
                )
            )
        )

        return top

    def gen_ipv4_config(self, params, key_map, operation):
        EN = nc_element_maker()
        EC = config_element_maker()

        config = EN.config(
            EC.top(
                EC.IPV4ADDRESS(
                    EC.Ipv4Addresses(
                        EC.Ipv4Address(
                            EC.IfIndex(self.interface.iface_index),
                            *config_params(params, key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def gen_ipv6_config(self, params, key_map, operation):
        EN = nc_element_maker()
        EC = config_element_maker()

        config = EN.config(
            EC.top(
                EC.IPV6ADDRESS(
                    EC.Ipv6AddressesConfig(
                        EC.AddressEntry(
                            EC.IfIndex(self.interface.iface_index),
                            *config_params(params, key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def get_config(self):
        """Return a list of currently configured IP addresses on the interface.

        Note:
            Either only IPv4 or only IPv6 addresses will be returned depending
            on the version stored in ``self.version``.

        Returns:
            A list of currently configured IP addresses on the interface.
        """
        if self.version == V4:
            top = self.gen_ipv4_top()
            addr_tag = 'Ipv4Address'
            mask_tag = 'Ipv4Mask'
            search_tag = 'Ipv4Address'
        elif self.version == V6:
            top = self.gen_ipv6_top()
            addr_tag = 'Ipv6Address'
            mask_tag = 'Ipv6PrefixLength'
            search_tag = 'AddressEntry'
        else:
            return {}

        key_map = {'addr': addr_tag,
                   'mask': mask_tag}

        nc_get_reply = self.device.get(('subtree', top))
        reply_data = findall_in_data(search_tag, nc_get_reply)

        existing_list = []
        for match in reply_data:
            to_dict = data_elem_to_dict(match, key_map)
            if to_dict:
                existing_list.append(to_dict)

        return existing_list

    def build(self, stage=False, **params):
        """Stage or execute a configuration to configure
        an IP address on an interface.

        Args:
            stage (bool): whether to stage the commands or execute
                immediately
            **params: see Keyword Args

        Keyword Args:
            addr (str): The IP address to add.
            mask (str): The network mask for the IP address,
                in dotted decimal or prefix length notation.

        Returns:
            True if stage=True and staging is successful
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='present', **params)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def remove(self, stage=False, **params):
        """Stage or execute a configuration to remove
        an IP address on an interface.

        Args:
            stage (bool): whether to stage the commands or execute
                immediately
            **params: see Keyword Args

        Keyword Args:
            addr (str): The IP address to remove.
            mask (str): The network mask for the IP address,
                in dotted decimal or prefix length notation.

        Returns:
            True if stage=True and staging is successful
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='absent', **params)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state='present', **params):
        """Build an etree.Element object to configure or remove
        an IP address on an interface.

        Args:
            state (str): 'present' to add an IP address,
                'absent' to remove an IP address.
            **params: see Keyword Args

        Keyword Args:
            addr (str): The IP address to add or remove.
            mask (str): The network mask for the IP address,
                in dotted decimal or prefix length notation.

        Returns:
            An etree.Element object to configure or remove
            an IP address on an interface.
        """
        address = params.get('addr')
        mask = params.get('mask')

        if not address or not mask:
            raise IpIfaceMissingData

        ip_obj = ipaddress.ip_network(address + '/' + mask)

        if self.version == V4:
            addr_tag = 'Ipv4Address'
            mask_tag = 'Ipv4Mask'
            params['mask'] = str(ip_obj.netmask)
        elif self.version == V6:
            addr_tag = 'Ipv6Address'
            mask_tag = 'Ipv6PrefixLength'
            params['mask'] = str(ip_obj.prefixlen)
            params['addr_origin'] = '1'
        else:
            return

        key_map = {'addr': addr_tag,
                   'mask': mask_tag,
                   'addr_origin': 'AddressOrigin'}

        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'remove'
            del params['mask']

        config = None
        if self.version == V4:
            config = self.gen_ipv4_config(params, key_map, operation)
        elif self.version == V6:
            config = self.gen_ipv6_config(params, key_map, operation)

        return config
