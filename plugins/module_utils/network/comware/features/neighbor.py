"""Gather LLDP neighbor information from COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, find_in_data)


class Neighbors(object):
    """Gather LLDP neighbor information from a COM7 switch.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        lldp (lldp): dictionary containing LLDP neighbors
        cdp (cdp): dictionary containing CDP neighbors

    """

    def __init__(self, device):

        self.device = device

        self.lldp = self._get_neighbors(ntype='lldp')
        self.cdp = self._get_neighbors(ntype='cdp')

    def _get_interface_from_index(self, index):
        """ Returns interface name based on a given ifindex
        """
        E = data_element_maker()
        top = E.top(
            E.Ifmgr(
                E.Interfaces(
                    E.Interface(
                        E.IfIndex(index),
                        E.Name()
                    )
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        interface_name = find_in_data('Name', nc_get_reply).text

        return interface_name

    def refresh(self):
        """Refreshes the "ldp" and "cdp" attributes of the class
        """

        self.lldp = self._get_neighbors(ntype='lldp')
        self.cdp = self._get_neighbors(ntype='cdp')

    def _get_neighbors(self, ntype='lldp'):
        """Gets neighbors of device (COM7)

            Args:
                ntype (str): must be "lldp" or "cdp"

            Returns:
                List of dicts with the following k/v pairs:
                    :local_intf (str): local interface of device
                    :neighbor_intf (str): remote interface of the neighbor
                        device
                    :neighbor (str): hostname of the neighbor device for lldp
                        and mgmt IP addr when cdp
        """
        E = data_element_maker()
        if ntype == 'cdp':
            top = E.top(
                E.LLDP(
                    E.CDPNeighbors(
                        E.CDPNeighbor()
                    )
                )
            )
        else:
            top = E.top(
                E.LLDP(
                    E.LLDPNeighbors(
                        E.LLDPNeighbor()
                    )
                )
            )

        nc_get_reply = self.device.get(('subtree', top))
        return self._build_response(nc_get_reply, ntype=ntype)

    def _build_response(self, nc_reply, ntype='lldp'):
        """Builds dictionary from XML response coming from device

        Args:
            nc_reply (lxml.etree._Element): NETCONF
                response from device as etree element

        Returns:
            It returns a list of dictionary objects and each neighbor
            is represented as a dictionary object with the following k/v
            pairs:
                :local_intf (str): local interface of device
                :neighbor_intf (str): remote interface of the neighbor
                    device
                :neighbor (str): hostname of the neighbor device for lldp
                    and mgmt IP addr when cdp
        """

        if ntype == 'lldp':
            key_map = {
                'neighbor': 'SystemName',
                'neighbor_intf': 'PortId',
            }
            neighbors = findall_in_data('LLDPNeighbor', nc_reply)
        else:
            key_map = {
                'neighbor': 'ManageAdress',
                'neighbor_intf': 'PortId',
            }
            neighbors = findall_in_data('CDPNeighbor', nc_reply)

        return_neigh = []

        for neigh in neighbors:
            temp = {}
            index = find_in_data('IfIndex', neigh).text
            interface = self._get_interface_from_index(index)
            temp['local_intf'] = interface
            for new_key, xml_tag in key_map.items():
                obj = find_in_data(xml_tag, neigh)
                if obj is not None:
                    value = obj.text
                    temp[new_key] = value
            return_neigh.append(temp)

        return return_neigh
