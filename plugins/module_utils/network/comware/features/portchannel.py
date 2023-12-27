"""Manage portchannels on COM7 devices.
"""
import base64

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    InvalidPortType, AggregationGroupError
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class Portchannel(object):
    """This class is used to collect data or configure a specific portchannel.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        groupid (str): group # of the RAGG/BAGG interface
        pc_type (str): must be "bridged" or "routed"


    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        groupid (str): group # of the RAGG/BAGG interface
        pc_type (str): must be "bridged" or "routed"
        members_to_remove (list): interface names to remove from the
            portchannel
        desired_lacp_mode (str): set to "active" or "passive".  Should be
            set when ``mode`` is set to the value of ``lacp``
            in ``build_config``.

    """

    def __init__(self, device, groupid, pc_type):
        self.device = device
        self.groupid = groupid
        self.pc_type = pc_type

        # maps to internal integer representing the LAGG
        # since user facing #'s can be equal, i.e. R-Agg1
        # and B-Agg1.  This is the unique value.
        self._xgroupid = self._pc_group_mapping()
        self.members_to_remove = []
        self.desired_lacp_mode = ''

        self._members_map_index_key = {}
        self._members_map_interface_key = {}
        self._members_groups = {}

        # list of XML tags used to build proper objects
        self.pc_tags = ['LAGG', 'LAGGGroups', 'LAGGGroup']
        self.member_tags = ['LAGG', 'LAGGMembers', 'LAGGMember']

        # The rest of the attributes listed below are all used to map
        # XML tags to dictionary keys (and vice versa) as well as
        # map values coming from the switch into more user friendly values
        self.PORTCHANNEL = dict(
            groupid='GroupId',
            mode='LinkMode',
            pc_index='IfIndex',
            members='MemberList',
            lacp_edge='LacpEdgeEnable',
            hash_mode='LoadSharingMode'
        )
        self.R_PORTCHANNEL = dict(reversed(item) for item in self.PORTCHANNEL.items())
        self.value_map = {
            'LinkMode': {
                '1': 'static',
                '2': 'dynamic'
            },
            'LacpEdgeEnable': {
                'true': 'enabled',
                'false': 'disabled'
            },
            'LoadSharingMode': {
                '2': 'destination-mac',
                '4': 'source-mac',
                '8': 'destination-ip',
                '16': 'source-ip'
            }
        }
        self.R_value_map = reverse_value_map(
            self.R_PORTCHANNEL, self.value_map)
        self.LACP = dict(
            groupid='GroupId',
            intf_index='IfIndex',
            enabled='LacpEnable',
            lacp_mode='LacpMode'
        )
        self.R_LACP = dict(reversed(item) for item in self.LACP.items())
        self.lacp_value_map = {
            'LacpMode': {
                '1': 'active',
                '2': 'passive'
            }
        }
        self.R_lacp_value_map = reverse_value_map(
            self.R_LACP, self.lacp_value_map)

    def get_portchannels(self):
        """Get a list of portchannel groups that exist on the switch

            Returns:
                This returns a list of numbers represented as strings
                that are the portchannel groups that exist on the switch.
        """
        E = data_element_maker()
        top = E.top(
            E.LAGG(
                E.LAGGGroups(
                    E.LAGGGroup(
                        E.IfIndex(),
                        E.GroupId(),
                        E.LinkMode(),
                        E.MemberList(),
                        E.LacpEdgeEnable(),
                        E.LoadSharingMode()
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        pc_groups_xml = findall_in_data('GroupId', nc_get_reply)

        groups = [group.text for group in pc_groups_xml]

        return groups

    def get_config(self):
        """Get current configuration for a given portchannel

        Returns:
            This returns a dictionary that has the following k/v pairs
            if the portchannel exists:

                :groupid (str): group ID of the portchannel
                :ncgroupid (str): INTERNAL group ID used by the switch
                    to differentiate between bridged, routed, and other types
                    of LAGGs. Kept to assist in troubleshooting.
                :mode (str): will be "static" or "dynamic"
                :members (list): list of current members by interface name
                :min_ports (str): number that represents selected-port minimum
                :max_ports (str): number that represents selected-port maximum
                :lacp_modes_by_interface (dict): list of dicts that have two
                    key/value pairs. sample_dict=(interface='FortyGigE1/0/1',
                    lacp_mode='passive')

            It returns an empty dictionary if the portchannel group does
            not exist.

        """
        E = data_element_maker()
        top = E.top(
            E.LAGG(
                E.LAGGGroups(
                    E.LAGGGroup(
                        E.GroupId(self._xgroupid)
                    )
                )
            )
        )
        nc_get_reply = self.device.get(('subtree', top))
        return_pc = data_elem_to_dict(nc_get_reply, self.PORTCHANNEL, value_map=self.value_map)

        if return_pc:
            return_pc['groupid'] = self.groupid
            return_pc['nc_groupid'] = self._xgroupid

            members = []
            members_by_index = []
            members_by_name = []

            if return_pc.get('members'):
                members_by_index, members_by_name = \
                    self._get_members_from_bitmap(return_pc.get('members'))

                # building dictionary that has keys that are IfIndex values
                # and has values that are the associated interface name
                for count, each in enumerate(members_by_index):
                    self._members_map_index_key[str(each)] = \
                        members_by_name[count]

                # building dictionary that has keys that are Interface names
                # and has values that are the associated IfIndex values
                for count, each in enumerate(members_by_name):
                    self._members_map_interface_key[each.lower()] = \
                        members_by_index[count]

                for memb in members_by_name:
                    mode = self.get_lacp_mode_by_name(name=memb)
                    temp = dict(interface=memb, lacp_mode=mode)
                    members.append(temp)

            return_pc['members'] = members_by_name
            return_pc['lacp_modes_by_interface'] = members

            self._get_pc_config_raw()

            return_pc['min_ports'] = self.get_selected_port_min()
            return_pc['max_ports'] = self.get_selected_port_max()
            return_pc['s_mlag'] = self.get_smlag()
            return_pc['speed'] = self.get_speed()
            return_pc['hash_mode'] = self.get_hash_mode()
        return return_pc

    def get_all_members(self, list_type='name', asdict=False):
        """Gets ports that are a member to any port channel

           Args:
               list_type (str): must be "name" or "ifindex"
               asdict (bool): determines if a dict should be returned
                   this overrides list_type (see Returns)

           Returns:
               1 of 4 objects can be returned based on input args:

                   if asdict=True regardless of other Args, a dict
                       is returned that has interface names as keys and
                       the group of the port-channel that is config'd on that
                       interface as the key
                    if list_type is name (default), a list of interface
                        names is returned.  The names of interfaces that
                        have any portchannel config'd.
                    if list_type is set to "ifindex", the list has all
                        ifindexes instead of names of interfaces that have
                        a portchannel config'd.
                    if list_type is misconfigured, an error string is returned.
        """
        E = data_element_maker()
        top = E.top(
            E.LAGG(
                E.LAGGMembers(
                    E.LAGGMember(
                        E.IfIndex(),
                        E.GroupId()
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        data = findall_in_data('LAGGMember', nc_get_reply)

        members_as_index = []
        members_as_name = []

        for each in data:
            index = find_in_data('IfIndex', each).text
            group = find_in_data('GroupId', each).text
            if group != '0':
                members_as_index.append(index)
                name = self.get_interface_from_index(index)
                members_as_name.append(name)
                self._members_groups[name] = group

        if asdict:
            return self._members_groups
        if list_type == 'name':
            return members_as_name
        elif list_type == 'ifindex':
            return members_as_index
        else:
            return 'invalid value for list_type'

    def get_lacp_mode_by_name(self, name):
        """Get current LACP mode for a given interface

           Args:
               name (str): full name of the interface

           Returns:
               mode (str): "active" or "passive"
        """
        E = data_element_maker()
        top = E.top(
            E.LAGG(
                E.LAGGMembers(
                    E.LAGGMember(
                        E.IfIndex(self.get_index_from_interface(name))
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        return_lacp = data_elem_to_dict(nc_get_reply, self.LACP, value_map=self.lacp_value_map)

        # if return_lacp.get('groupid') != '0':
        #    return_lacp['groupid'] = self.groupid

        return return_lacp.get('lacp_mode')

    def _get_members_from_bitmap(self, bitmap):
        """Return list of interface names from bitmap encoded as base64

            Args:
                bitmap (str): memberlist as base64 as retrieved via NETCONF

            Returns:
                This returns a list of interface names.

        """

        # hex_value = base64.b64decode(bitmap).decode('utf-8')
        print('bitmap = ', bitmap)
        # bitmap = str(base64.b64encode(bitmap.encode("utf-8")), "utf-8")
        # hex_value = str(base64.b64decode(bitmap), "utf-8")
        hex_value = base64.b64decode(bitmap).hex()
        print('hex_value = ', hex_value)
        h_size = len(hex_value) * 4
        binary_value = (bin(int(hex_value, 16))[2:]).zfill(h_size)

        print('binary_value = ', binary_value)
        members_by_index = []
        for index, bit in enumerate(binary_value):
            port = index + 1
            if bit == '1':
                members_by_index.append(port)
        members_by_name = []
        for index in members_by_index:
            members_by_name.append(self.get_interface_from_index(str(index)))

        return members_by_index, members_by_name

    #    def _get_bitmap_from_members(self, members):
    #        """Return bitmap given a list of interface names
    #           Not used, but kept, just in case :)
    #        """
    #        index_list = []
    #        for member in members:
    #            index = self.get_index_from_interface(member)
    #            index_list.append(int(index))
    #
    #        index_list.sort()
    #        binary = ''
    #        start = 1
    #        for finish in index_list:
    #            for num in range(start, finish):
    #                binary += '0'
    #            binary += '1'
    #            start = finish + 1
    #
    #        lenbinary = len(binary)
    #        start = 8
    #        while (start % lenbinary) == start:
    #            start += 8
    #        newfill = start - len(binary)
    #        binary += newfill * '0'
    #
    #        # chr only goes up to 255!!! fixed in py3!!! ugh
    #        # bitmap = base64.b64encode(chr(int(binary, 2)))
    #        hexa = hex(int(binary, 2))[2:]
    #        if len(hexa) % 2 != 0:
    #            hexa += '0'
    #        converted_to_ascii = binascii.a2b_hex(hexa)
    #        bitmap = base64.b64encode(converted_to_ascii)
    #
    #        return bitmap
    def get_interface_from_index(self, index):
        """Return interface name based on a given ifindex
        """
        E = data_element_maker()
        top = E.top(
            E.Ifmgr(
                E.Interfaces(
                    E.Interface(
                        E.IfIndex(index)
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        interface_name = find_in_data('Name', nc_get_reply).text

        return interface_name

    def _pc_group_mapping(self):
        """Map user input for portchannel group to the internal integer
           used by the system, since the user can create a routed-agg with
           group 1 and bridged-group with group 1. This maps the group to the
           "real" group used internally
        """

        group = int(self.groupid)
        if self.pc_type == 'bridged':
            self._xgroupid = group
        elif self.pc_type == 'routed':
            self._xgroupid = group + 16384
        return str(self._xgroupid)

    def _get_pc_config_raw(self):
        """Get raw text from CLI current configuration for the portchannel
        """
        if self.pc_type == 'bridged':
            self.fulltype = 'Bridge-Aggregation'
        elif self.pc_type == 'routed':
            self.fulltype = 'Route-Aggregation'

        text = self.device.cli_display(
            'display current-configuration interface {0} {1}'.format(
                self.fulltype, self.groupid))

        text_as_list = text.split('\n')

        self.raw_config = text_as_list

    def get_selected_port_min(self):
        """Get selected port min configuration

            Returns:
                This returns the selected-port minimum
                configured value on the switch, else it returns None

        """
        if not self.raw_config:
            self._get_pc_config_raw()

        find = 'selected-port minimum'
        for each in self.raw_config:
            if find in each:
                min_value = each.split(find)[-1].strip()
                return min_value

        return None

    def get_selected_port_max(self):
        """Get selected port max configuration

            Returns:
                This returns the selected-port maximum
                configured value on the switch, else it returns None
        """
        if not self.raw_config:
            self._get_pc_config_raw()

        find = 'selected-port maximum'
        for each in self.raw_config:
            if find in each:
                max_value = each.split(find)[-1].strip()
                return max_value
        return None

    # gqy
    def get_smlag(self):
        if not self.raw_config:
            self._get_pc_config_raw()

        find = 'port s-mlag group'
        for each in self.raw_config:
            if find in each:
                smlag_value = each.split(find)[-1].strip()
                return smlag_value

        return None

    def get_hash_mode(self):
        if not self.raw_config:
            self._get_pc_config_raw()

        find = 'load-sharing mode'
        for each in self.raw_config:
            if find in each:
                hash_mode = each.split(find)[-1].strip()
                return hash_mode

        return None

    def get_speed(self):
        if not self.raw_config:
            self._get_pc_config_raw()
        find = 'lacp select speed'

        return find

    def _get_min_max_smlag_cmds(self, **portchannel):
        """Get commands required to config min/max ports

            Args:
                portchannel: see Keyword Args

            Keyword Args:
                min_ports: value to set for selected-port minimum
                max_ports: value to set for selected-port maximum

        """
        min_links = portchannel.get('min_ports')
        max_links = portchannel.get('max_ports')
        smlag = portchannel.get('s_mlag')
        rate = portchannel.get('speed')
        commands = []
        cmd_1 = 'link-aggregation selected-port'
        cmd_2 = 'port s-mlag'
        cmd_3 = 'lacp select speed'
        if min_links:
            command_1 = cmd_1 + ' minimum {0}'.format(min_links)
            if command_1:
                commands.append(command_1)
        if max_links:
            command_1 = cmd_1 + ' maximum {0}'.format(max_links)
            if command_1:
                commands.append(command_1)
        if smlag:
            command_2 = cmd_2 + ' group {0}'.format(smlag)
            if command_2:
                commands.append(command_2)
        if rate:
            commands.append(cmd_3)
        if min_links or max_links or smlag or rate:
            commands.insert(0, 'interface {0} {1}'.format(self.fulltype,
                                                          self.groupid))
        return commands

    def get_index_from_interface(self, interface):
        """Get IfIndex from interface name

            Args:
                interface (str): name of the interface

            Returns:
                This returns the IfIndex for an interface.

        """

        local_index = self._members_map_interface_key.get(interface)
        if local_index:
            index = local_index
        else:
            intf = Interface(self.device, interface)
            index = str(intf.iface_index)
            self._members_map_interface_key[interface] = index

        return index

    def _add_lagg_member(self, interface, remove=False, lacp=None):
        """Add lagg member to an XML object element
        """
        if remove:
            group = '0'
        else:
            group = self._xgroupid

        E = config_element_maker()

        lacp_args = []
        if lacp:
            lacp_args.append(E.LacpMode(lacp))

        member = E.LAGGMember(
            E.IfIndex(self.get_index_from_interface(interface)),
            E.GroupId(group),
            *lacp_args
        )

        return member

    def remove(self, stage=False):
        """Stage or execute a config object to remove portchannel

        Args:
            stage (bool): whether to stage the commands or execute
                immediately

        Returns:
            True if stage=True and successfully staged
            List of etree.Element XML responses if immediate execution
        """
        return self._build_config(state='absent', stage=stage)

    def build(self, stage=False, **portchannel):
        """Stage or execute a config object to add/update portchannel

        Args:
            state (str): must be "present" or "absent"
            portchannel: see Keyword Args
            stage (bool): whether to stage the commands or execute
                immediately

        Keyword Args:
            members (list): OPTIONAL - list of members by interface name
                being configured
            min_ports (str): OPTIONAL - number that represents
                selected-port minimum
            max_ports (str): OPTIONAL - number that represents
                selected-port maximum
            lacp_to_change (list): OPTIONAL - list of interfaces that need
                have their lacp mode changed

        Note:
            ``desired_lacp_mode`` needs to be set for the members in
            ``portchannel['lacp_to_change']`` to take effect.

            ``members_to_remove`` can be set to remove members during the
            build process.  This should also be a list of interface names.

        Returns:
            True if stage=True and successfully staged
            List of etree.Element XML responses if immediate execution
        """
        return self._build_config(state='present', stage=stage, **portchannel)

    def _build_config(self, state, stage=False, **portchannel):
        """Stage or execute a config object to add/update portchannel

        Args:
            stage (bool): whether to stage the commands or execute
                immediately

        Returns:
            True if stage=True and successfully staged
            List of etree.Element XML responses if immediate execution
        """
        operation = None
        if state == 'present':
            operation = 'merge'
        elif state == 'absent':
            operation = 'delete'

        # needs to be the "internal" id, not user exposed id
        portchannel['groupid'] = self._xgroupid

        EC = nc_element_maker()
        E = config_element_maker()

        members_desired_list = portchannel.get('members') or []

        # removing members b/c it messes with the value map
        if 'members' in portchannel.keys():
            portchannel.pop('members')

        config = EC.config(
            E.top(
                E.LAGG(
                    E.LAGGGroups(
                        E.LAGGGroup(
                            *config_params(portchannel, self.PORTCHANNEL, value_map=self.R_value_map, fill_in=False)
                        )
                    )
                ),
                **operation_kwarg(operation)
            )
        )

        lacp_to_change = portchannel.get('lacp_to_change')

        if state == 'present':
            if members_desired_list or self.members_to_remove or \
                    lacp_to_change:
                lagg = find_in_config('LAGG', config)
                members = E.LAGGMembers()
                # member = etree.Element(qualify('LAGGMember', NCCONFIG))
                # if members_as_passed_in:
                for each in members_desired_list:
                    members.append(self._add_lagg_member(each))
                # now remove any members not in the desired members list
                # and set in the remove list
                for each in self.members_to_remove:
                    members.append(self._add_lagg_member(each, remove=True))
                if lacp_to_change:
                    for each in lacp_to_change:
                        value = self.R_lacp_value_map.get('lacp_mode').get(
                            self.desired_lacp_mode)
                        member = self._add_lagg_member(each, lacp=value)
                        members.append(member)

                lagg.append(members)

        # stages the native NETCONF XML Objects
        c1 = True
        c2 = True
        if stage:
            c1 = self.device.stage_config(config, 'edit_config')
        else:
            c1 = self.device.edit_config(config)

        # configuring the min and max ports not possible via NETCONF
        # Use CLI via NETCONF instead, separate staging happening here too
        if portchannel.get('min_ports') or portchannel.get('max_ports') or portchannel.get('s_mlag') or portchannel.get(
                'speed'):
            self._get_pc_config_raw()
            min_max_smalg = self._get_min_max_smlag_cmds(**portchannel)

            if min_max_smalg:
                if stage:
                    c2 = self.device.stage_config(min_max_smalg, 'cli_config')
                else:
                    c2 = self.device.cli_config(min_max_smalg)
        if stage:
            return c1 and c2
        else:
            return [c1, c2]

    def param_check(self, **portchannel):
        """Param validation for portchannel

            Args:
                state (str): present or absent
                portchannel: see Keyword Args

            Keyword Args:
                members (list): members by interface name being configured

            Raises:
                InvalidPortType: when existing port type does not match
                    desired type of portchannel
                AggregationGroupError: when an interface is already
                    a member of a different portchannel than the
                    one being configured.

        """
        if portchannel.get('members'):
            members = portchannel.get('members')
            for each in members:
                interf = Interface(self.device, each)
                configured_type = interf.get_config().get('type')
                #                if configured_type == 'bridged':
                #                    configured_type = 'bridged'
                if configured_type != self.pc_type:
                    raise InvalidPortType(each, configured_type,
                                          self.pc_type)
                member_dict = self.get_all_members(asdict=True)
                existing_group = member_dict.get(each)
                if existing_group:
                    if existing_group != self._xgroupid:
                        raise AggregationGroupError(each)
