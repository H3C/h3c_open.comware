"""Manage VLANS on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    LengthOfStringError, VlanIDError
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    operation_kwarg, config_params)


class Vlan(object):
    """This class is used to get data and configure a specific VLAN.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vlanid (str): VLAN ID

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vlanid (str): VLAN ID

    """

    def __init__(self, device, vlanid=None):
        self.device = device
        if vlanid:
            self.vlanid = vlanid

        # dictionary to XML tag mappings
        self.vlan_key_map = {
            'vlanid': 'ID',
            'name': 'Name',
            'descr': 'Description'
        }

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.top(
            E.VLAN(
                E.VLANs(
                    E.VLANID()
                )
            )
        )

        return top

    def get_vlan_list(self):
        """Get a list of VLAN IDs that exist on the switch.

        Returns:
            It returns a list of VLAN IDs as strings.
        """
        top = self.gen_top()
        nc_get_reply = self.device.get(('subtree', top))
        vlans_xml = findall_in_data('ID', nc_get_reply.data_ele)
        vlans = [vlan.text for vlan in vlans_xml]

        return vlans

    def get_config(self):
        """Gets current configuration for a given VLAN ID

        Args:
            vlanid (str): REQUIRED - VLAN ID

        Returns:
            This returns a dictionary with the following
                k/v pairs:

                :vlanid (str): VLAN ID of the vlan requested
                :name (str): configured name of the vlan
                :descr (str): configured descr of the vlan

            It returns an empty dictionary if the vlan does not exist
        """
        top = self.gen_top()
        vlan_id_ele = find_in_data('VLANID', top)
        vlan_id_ele.append(data_element_maker().ID(self.vlanid))

        nc_get_reply = self.device.get(('subtree', top))
        vlan_config = data_elem_to_dict(nc_get_reply, self.vlan_key_map)

        return vlan_config

    def remove(self, stage=False):
        """Stage or execute XML object for VLAN removal and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='absent')
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def build(self, stage=False, **vlan):
        """Stage or execute XML object for VLAN configuration and send to staging

        Args:
            stage (bool): whether to stage the command or execute immediately
            vlan: see Keyword Args

        Keyword Args:
            name (str): OPTIONAL - VLAN name
            descr (str): OPTOINAL - VLAN description

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        config = self._build_config(state='present', **vlan)
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)

    def _build_config(self, state, **vlan):
        """Build XML object for VLAN configuration

        Args:
            state (str): OPTIONAL must be "present" or "absent"
                DEFAULT is "present"
            vlan: see Keyword Args

            Keyword Args:
                name (str): OPTIONAL - VLAN name
                descr (str): OPTOINAL - VLAN description

        Returns:
            XML object for VLAN configuration
        """
        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'delete'

        EC = nc_element_maker()
        E = config_element_maker()

        vlan['vlanid'] = self.vlanid
        config = EC.config(
            E.top(
                E.VLAN(
                    E.VLANs(
                        E.VLANID(
                            *config_params(vlan, self.vlan_key_map)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def param_check(self, **vlan):
        """Basic param validation for vlan

        Args:
            state (str): REQUIRED must be "present" or "absent"
            vlan: see Keyword Args

            Keyword Args:
                vlanid (str): OPTIONAL - VLAN ID
                name (str): OPTIONAL - VLAN name
                descr (str): OPTIONAL - VLAN description

        """
        try:
            vlanid = int(self.vlanid)
        except ValueError:
            raise VlanIDError
        if vlanid < -1 or vlanid > 4094:
            raise VlanIDError

        descr = vlan.get('descr')
        if descr and len(descr) > 254:
            raise LengthOfStringError("'descr'")

        name = vlan.get('name')
        if name and len(name) > 32:
            raise LengthOfStringError("'name'")
