"""Manage VXLAN configurations on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.templates import cli
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, findall_in_data, find_in_data, data_elem_to_dict, nc_element_maker, config_element_maker,
    operation_kwarg, reverse_value_map)
tunnel_tmpl = r"""Value MODE (\w+)
Value SRC (((\d+.){3}\d+))
Value DEST (((\d+.){3}\d+))

Start
  ^interface Tunnel\d+\s+mode\s+${MODE}
  ^\s+source\s${SRC}
  ^\s+destination\s${DEST} -> Record
"""


class Tunnel(object):
    """This class is used to get data and configure VXLAN tunnel interfaces.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        tunnel (str): Tunnel ID

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        tunnel (str): Tunnel ID

    """

    def __init__(self, device, tunnel):

        self.device = device
        self.tunnel = tunnel

        # mapping of dictionary keys to XML tags
        self.TUNNELS = {
            'tunnel': 'TunnelID',
            'vxlan': 'VxlanID'
        }

    def get_config(self):
        """Get running config for a tunnel interface

        Returns:
            A dictionary is returned with the following k/v pairs:
                src (str): source IP addr of tunnel
                dest (str): destination IP addr of tunnel
                mode (str): mode of tunnel

            If the tunnel does not exist, an empty dictionary is returned.

        """
        existing = {}
        config = self.device.cli_display(
            'display current-configuration interface Tunnel {0}'.format(
                self.tunnel))

        parsed = cli.get_structured_data(tunnel_tmpl, config)

        if not parsed:
            existing = {}  # i.e, does not exist
        else:
            if len(parsed) == 1:  # which it should!
                existing = parsed[0]

        return existing

    def get_global_source(self):
        """Get global source address for tunnel interfaces

        Returns:
            String that is the global source IP address on the switch
        """
        address = None
        config = self.device.cli_display(
            'display current-configuration | inc "tunnel global source"')
        config_list = config.split('\n')
        if len(config_list) == 2:
            return None
        else:
            for each in config_list:
                if 'tunnel global' in each:
                    address = each.split(
                        'tunnel global source-address')[-1].strip()
        return address

    def build(self, stage=False, **kvargs):
        """Stage or execute config object to create/update tunnel

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            CLI response strings if immediate execution
        """
        return self._build_config(state='present', stage=stage, **kvargs)

    def remove(self, stage=False):
        """Build config object to remove tunnel interface

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            CLI response strings if immediate execution
        """
        return self._build_config(state='absent', stage=stage)

    def _build_config(self, state, stage=False, **kvargs):
        """Build CLI commands to configure/create VXLAN tunnel interfaces

        Args:
            state (str): must be "absent" or "present"
            kvargs: see Keyword Args
            stage (bool): whether to stage the command or execute immediately

        Keyword Args:
            src (str): OPTIONAL - source IP addr of tunnel
            dest (str): OPTIONAL - destination IP addr of tunnel
            global_src (str): OPTIONAL - global src IP addr for tunnels

        Returns:
            True if stage=True and successfully staged
            CLI response strings if immediate execution
        """
        commands = []
        if state == 'absent':
            commands.append('undo interface tunnel {0}'.format(self.tunnel))
        elif state == 'present':
            if kvargs.get('global_src'):
                commands.append('tunnel global source-address {0}'.format(
                    kvargs.get('global_src')))
            # has a not kvargs because tunnel ID won't be in there
            # if it's a new tunnel when using Ansible
            if kvargs.get('src') or kvargs.get('dest') or not kvargs:
                commands.append('interface tunnel {0} mode vxlan'.format(
                    self.tunnel))
                if kvargs.get('src'):
                    commands.append('source {0}'.format(kvargs.get('src')))
                if kvargs.get('dest'):
                    commands.append('destination {0}'.format(
                        kvargs.get('dest')))

        if commands:
            if stage:
                self.device.stage_config(commands, 'cli_config')
            else:
                self.device.cli_config(commands)


class Vxlan(object):
    """This class is used to get data and configure VXLAN/VSI mappings.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vxlan (str): VXLAN ID
        vsi (str): name of the VSI

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        vxlan (str): VXLAN ID
        vsi (str): name of the VSI

    """

    def __init__(self, device, vxlan, vsi=None):

        self.device = device
        self.vxlan = vxlan
        self.vsi = vsi
        self.VSI = {
            'vsi': 'VsiName',
            'descr': 'Description',
        }

        # mapping of dictionary keys to XML tags
        self.VXLAN = {
            'vxlan': 'VxlanID',
            'vsi': 'VsiName',
        }
        # mapping of dictionary keys to XML tags
        self.TUNNELS = {
            'tunnel': 'TunnelID',
            'vxlan': 'VxlanID'
        }

    def get_config(self):
        """Get associated VSI for a given VXLAN ID along with configured
        tunnels for that given VXLAN/VSI mapping.

        Returns:
            Dictionary with the following key/value pairs:
                :vxlan (str): vxlan id
                :vsi (str): name of vsi

            If the mapping does not exist, an empty dictionary is returned.

        """
        E = data_element_maker()
        top = E.top(
            E.VXLAN(
                E.VXLANs(
                    E.Vxlan(
                        E.VxlanID(self.vxlan)
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        return_vxlan = data_elem_to_dict(nc_get_reply, self.VXLAN)

        if return_vxlan:
            return_vxlan['tunnels'] = self.get_tunnels()

        return return_vxlan

    def _build_vsi(self, operation, vsi=None):
        """Builds object to create/delete a VSI

        Args:
            operation (str): "merge" or "delete"

        Keyword Args:
            vsi (str): name of VSI

        Returns:
            etree.Element config object to create/delete VSI
        """
        if not vsi:
            vsi = self.vsi

        EN = nc_element_maker()
        EC = config_element_maker()

        config = EN.config(
            EC.top(
                EC.L2VPN(
                    EC.VSIs(
                        EC.VSI(
                            EC.VsiName(vsi)
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def _build_vxlan(self, operation):
        """Creates object to create a VXLAN and associate to a VSI name

        Args:
            operation (str): "merge" or "delete"
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        vsi_name_ele = []
        if operation == 'merge':
            vsi_name_ele.append(EC.VsiName(self.vsi))

        config = EN.config(
            EC.top(
                EC.VXLAN(
                    EC.VXLANs(
                        EC.Vxlan(
                            EC.VxlanID(self.vxlan),
                            *vsi_name_ele
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def _build_tunnels(self, operation, tunnels):
        """Updates tunnel objects for a given VXLAN/VSI

            Args:
                operation (str): "merge" or "delete"
                tunnels (list): list of tunnel ID (strings) to be modified
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        tunnel_eles = []
        for tunnel in tunnels:
            tunnel_eles.append(EC.Tunnel(EC.TunnelID(tunnel), EC.VxlanID(self.vxlan)))

        config = EN.config(
            EC.top(
                EC.VXLAN(
                    EC.Tunnels(*tunnel_eles),
                    **operation_kwarg(operation)
                )
            )
        )

        return config

    def build(self, stage=False, **kvargs):
        """Stage or execute config for managing tunnels

        Args:
            stage (bool): whether to stage the command or execute immediately
            kvargs: see Keyword Args
            stage (bool): whether to stage the command or execute immediately

        Keyword Args:
            tunnels_to_add (list): OPTIONAL - tunnels to add to the VXLAN/VSI
                mapping
            tunnels_to_remove (list): OPTIONAL - tunnels to remove to the
                VXLAN/VSI mapping

        Returns:
            True if stage=True and successfully staged
            List of etree.Element XML responses if immediately executed
        """
        rmv = True
        add = True

        if kvargs.get('tunnels_to_remove'):
            rmv_config = self._build_tunnels('delete', kvargs.get('tunnels_to_remove'))
            if stage:
                rmv = self.device.stage_config(rmv_config, 'edit_config')
            else:
                rmv = self.device.edit_config(rmv_config)

        if kvargs.get('tunnels_to_add'):
            add_config = self._build_tunnels('merge', kvargs.get('tunnels_to_add'))
            if stage:
                add = self.device.stage_config(add_config, 'edit_config')
            else:
                add = self.device.edit_config(add_config)

        if stage:
            return rmv and add
        else:
            return [rmv, add]

    def create(self, stage=False):
        """Stage or execute a config for creating a VSI

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            List of etree.Element XML responses if immediately executed
        """
        vsi_config = self._build_vsi('merge')
        vxlan_config = self._build_vxlan('merge')

        if stage:
            vsi = self.device.stage_config(vsi_config, 'edit_config')
            vxlan = self.device.stage_config(vxlan_config, 'edit_config')
        else:
            vsi = self.device.edit_config(vsi_config)
            vxlan = self.device.edit_config(vxlan_config)

        if stage:
            return vsi and vxlan
        else:
            return [vsi, vxlan]

    def remove_vsi(self, stage=False, vsi=None):
        """Stage or execute a config for removing a VSI

        Args:
            stage (bool): whether to stage the command or execute immediately
            vsi (dict): vsi parameters

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediately executed
        """
        vsi_config = self._build_vsi('delete', vsi)
        if stage:
            vsi = self.device.stage_config(vsi_config, 'edit_config')
        else:
            vsi = self.device.edit_config(vsi_config)

        return vsi

    def remove_vxlan(self, stage=False):
        """Stage or execute a config for removing a VXLAN

        Args:
            stage (bool): whether to stage the command or execute immediately

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediately executed
        """
        vlan_config = self._build_vxlan('delete')
        if stage:
            vlan = self.device.stage_config(vlan_config, 'edit_config')
        else:
            vlan = self.device.edit_config(vlan_config)

        return vlan

    def get_tunnels(self):
        """Get a list of tunnel interface that are mapped to a given VXLAN ID

        Returns:
            List of tunnel IDs

        """
        E = data_element_maker()
        top = E.top(
            E.VXLAN(
                E.Tunnels(
                    E.Tunnel(
                        E.VxlanID(self.vxlan)
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        tunnels_xml = findall_in_data('Tunnel', nc_get_reply)

        tunnels = []
        for tunnel in tunnels_xml:
            tunnels.append(find_in_data('TunnelID', tunnel).text)

        return tunnels


class L2EthService(object):
    """This class is used to get data and configure Ethernet Service Instances
        on Layer 2 interfaces, map to VSI, and perform equiv of xconnect.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface (str): name of a Layer 2 interface
        instance (str): service instance ID to be configured on the
            interface
        vsi (str): name of the VSI being mapped to the instance

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        interface (str): name of a Layer 2 interface
        instance (str): service instance ID to be configured on the
            interface
        vsi (str): name of the VSI being mapped to the instance

    """

    def __init__(self, device, interface, instance, vsi):

        self.device = device
        self.interface = interface
        self.vsi = vsi
        self.instance = instance

        # the next few attributes map dictionary keys to XML tags
        # and maps XML values to more user-friendly values
        self.AC_KEY_MAP = {
            'vsi': 'VsiName',
            'index': 'IfIndex',
            'instance': 'SrvID',
            'access_mode': 'AccessMode',
        }
        self.AC_VALUE_MAP = {
            'AccessMode': {
                '1': 'vlan',
                '2': 'ethernet'
            }
        }
        self.RV_KEY_MAP = {
            'index': 'IfIndex',
            'instance': 'SrvID',
            'encap': 'Encap',
            'vlanid': 'SVlanRange',
            'cvid': 'CVlanRange'
        }
        self.RV_VALUE_MAP = {
            'Encap': {
                '1': 'default',
                '2': 'untagged',
                '3': 'tagged',
                '4': 's-vid',
                '5': 'only-tagged',
                '6': 'SvlanIdCvlanId',
                '7': 'CvlanId',
                '8': 'CvlanList',
                '9': 'SvlanIdCvlanList',
                '10': 'SvlanIdCvlanAll',
                '11': 'SvlanList',
                '12': 'SvlanListOnlyTagged',
            }
        }

        """
        supported value definition when using Ansible
        encapsulation default - 1
        encapsulation s-vid VLAN_ID - 4, but adds SVlanRange key as VLAN_ID
        encapsulation s-vid VLAN_ID only-tagged - 5,
                 but adds SVlanRange key as VLAN_ID
        encapsulation tagged - 3
        encapsulation untagged - 2
        """

    def get_config(self):
        """Get config of a service instance on a given interface for a
            given VSI

        Returns:
            If the mapping exists, it returns a dictionary with the
            following key/value pairs:
                :index (str): value of IfIndex
                :interface (str): name of interface
                :vsi (str): name of VSI
                :instance (str): instance ID
                :encap (str): ['default', 'untagged', 'tagged', 's-vid',
                    'only-tagged']
                :vlanid (str): vlanid PRESENT when ``encap`` set to
                    "only-tagged" or "s-vid"
                :access_mode (str): "vlan" or "ethernet"

        """
        existing = {}
        existing.update(self.get_vsi_encap())
        if existing:
            existing.update(self.get_vsi_map())
        return existing

    def vsi_exist(self):
        """Check to see if the VSI exists

        Returns:
            returns True if the VSI exists, else false

        """
        E = data_element_maker()
        top = E.top(
            E.L2VPN(
                E.VSIs(
                    E.VSI(
                        E.VsiName(self.vsi)
                    )
                )
            )
        )

        VSI = {
            'vsi': 'VsiName',
        }

        nc_get_reply = self.device.get(('subtree', top))
        return_map = data_elem_to_dict(nc_get_reply, VSI)

        return return_map

    def get_vsi_map(self):
        """Get xconnect config for given interface and service instance

        Returns:
            If the mapping exists, it returns a dictionary with the
            following key/value pairs:
                :index (str): value of IfIndex
                :vsi (str): name of VSI
                :interface (str): name of interface
                :instance (str): instance ID
                :access_mode (str): "vlan" or "ethernet"

        """
        E = data_element_maker()
        top = E.top(
            E.L2VPN(
                E.ACs(
                    E.AC(
                        E.SrvID(self.instance),
                        E.IfIndex(self._index_from_interface(self.interface))
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        return_map = data_elem_to_dict(
            nc_get_reply, self.AC_KEY_MAP, value_map=self.AC_VALUE_MAP)

        return return_map

    def get_vsi_encap(self):
        """Gets encap configuration for a given VXLAN ID

        Returns:
            If a config exists, it returns a dictionary with the
            following key/value pairs:
                :index (str): value of IfIndex
                :instance (str): instance ID
                :encap (str): ['default', 'untagged', 'tagged', 's-vid',
                    'only-tagged']
                :vlanid (str): vlanid PRESENT when ``encap`` set to
                    "only-tagged" or "s-vid"
        """
        E = data_element_maker()
        top = E.top(
            E.L2VPN(
                E.SRVs(
                    E.SRV(
                        E.SrvID(self.instance),
                        E.IfIndex(self._index_from_interface(self.interface))
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        return_vsi = data_elem_to_dict(
            nc_get_reply, self.RV_KEY_MAP, value_map=self.RV_VALUE_MAP)

        if return_vsi:
            return_vsi['interface'] = self._get_interface_from_index(
                return_vsi.get('index'))

        return return_vsi

    def _build_encap(self, operation, stage=False, **kvargs):
        """Stage or execute encap (service instance) config object for an interface

        Args:
            state (str): "present" or "absent"
            kvargs: see Keyword Args
            stage (bool): whether to stage the command or execute immediately

        Keyword Args:
            encap (str): 'default', 'tagged', 'untagged', 'only-tagged',
                's-vid'
            vlanid (str): REQUIRED if encap is set to only-tagged or s-vid

        Note:
            when encap is set to only-tagged, it also ensures s-vid

        Returns:
            True if stage=True and successfully staged
            etree.Element XML responses if immediately executed
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        encap_eles = []
        if operation == 'merge':

            REVERSE_RV_KEY_MAP = dict(reversed(
                item) for item in self.RV_KEY_MAP.items())

            REVERSE_RV_VALUE_MAP = reverse_value_map(
                REVERSE_RV_KEY_MAP, self.RV_VALUE_MAP)

            encap = kvargs.get('encap')
            vlanid = kvargs.get('vlanid')
            if encap:
                if encap in ['default', 'tagged', 'untagged']:
                    value = REVERSE_RV_VALUE_MAP.get('encap').get(
                        kvargs.get('encap'))
                    encap_eles.append(EC.Encap(value))
                elif encap in ['s-vid', 'only-tagged']:
                    encap_eles.append(EC.SVlanRange(vlanid))
                    if encap == 's-vid':
                        encap_eles.append(EC.Encap('4'))
                    elif encap == 'only-tagged':
                        encap_eles.append(EC.Encap('5'))

        self.jindex = self._index_from_interface(self.interface)  # minor hack for now

        config = EN.config(
            EC.top(
                EC.L2VPN(
                    EC.SRVs(
                        EC.SRV(
                            EC.SrvID(self.instance),
                            EC.IfIndex(self.jindex),
                            *encap_eles
                        )
                    ),
                    **operation_kwarg(operation)
                )
            )
        )

        if stage:
            self.device.stage_config(config, 'edit_config')
        else:
            self.device.edit_config(config)

    def remove(self, stage=False):
        """Stage or execute object to remove service instance configuration

        Args:
            stage (bool): whether to stage the command or execute immediately
        """
        self._build_config(state='absent', stage=stage)

    def build(self, stage=False, **kvargs):
        """Builds service instance (and xconn) config object for an interface
        Args:
            stage (bool):
            kvargs: see Keyword Args

        Keyword Args:
            vsi (str): OPTIONAL - name of VSI
            instance (str): OPTIONAL - instance ID
            encap (str): REQUIRED - ['default', 'untagged', 'tagged',
                's-vid', 'only-tagged']
            vlanid (str): REQUIRED when ``encap`` set to
               "only-tagged" or "s-vid"
            access_mode (str): OPTIONAL - "vlan" or "ethernet"

        Note: when encap is set to only-tagged, it also ensures s-vid
        """
        return self._build_config(state='present', stage=stage, **kvargs)

    def _build_config(self, state, stage=False, **kvargs):
        """Stage or execute service instance (and xconn) config object for an interface

        Args:
            stage (bool): whether to stage the command or execute immediately
        """
        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'delete'

        self._build_encap(operation, stage=stage, **kvargs)

        if operation == 'merge':
            # needs to happen AFTER
            self._build_xconnect(self.jindex, stage=stage, **kvargs)

    def _build_xconnect(self, index, stage=False, **kvargs):
        """Stage or execute config object to configure the equivalent of the xconnect
        command

        Args:
            index (str): IfIndex of the interface being configured
            stage (bool): whether to stage the command or execute immediately
            kvargs: see Keyword Args

        Keyword Args:
            access_mode (str): "vlan" or "ethernet"

        Returns:
            True if stage=True and successfully staged
            etree.Element XML responses if immediately executed
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        MAP = {
            'vlan': '1',
            'ethernet': '2'
        }

        config = EN.config(
            EC.top(
                EC.L2VPN(
                    EC.ACs(
                        EC.AC(
                            EC.SrvID(self.instance),
                            EC.IfIndex(index),
                            EC.VsiName(self.vsi),
                            EC.AccessMode(MAP.get(kvargs.get('access_mode')))
                        )
                    )
                )
            )
        )

        if stage:
            self.device.stage_config(config, 'edit_config')
        else:
            self.device.edit_config(config)

    def _index_from_interface(self, interface):
        """Returns IfIndex from a given Interface name
        """
        intf = Interface(self.device, interface)
        return intf.iface_index

    def _get_interface_from_index(self, index):
        """ Returns interface name based on a given IfIndex
        """
        interface_name = None
        if index:
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
