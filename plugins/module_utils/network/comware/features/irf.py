"""This module is used to configure IRF for a
``COM7`` device. The ``IRFMember`` class is used
to change the IRF member numbers on the device, and
can force a reboot. The ``IRFPort`` class is used to
bind physical ports to IRF ports. ``IRFMember`` should
be used first and the ``IRFPort``.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    InterfaceAbsentError,
    IRFMemberDoesntExistError)


class IrfPort(object):
    """This class is used to get and build IRF port configurations
    on a ``COM7`` device.

    Args:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.

    Attributes:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
    """
    def __init__(self, device):
        self.device = device

    def _build_iface_updown(self, iface_list, updown):
        """Stage commands to bring the interfaces up or down.
        """
        for iface_name in iface_list:
            iface = Interface(self.device, iface_name)
            if not iface.iface_exists:
                raise InterfaceAbsentError(iface.interface_name)
            iface.build(stage=True, admin=updown)

    def build(self, member_id, old_p1=None, old_p2=None,
              irf_p1=None, irf_p2=None,
              filename='startup.cfg',
              activate=True):
        """Stage all the commands to configure IRF ports, including:
        1. Bringing down interfaces to be removed or added
        2. Binding physical ports to IRF ports
        3. Bringing up interfaces to be added.
        4. Saving the config.
        5. (Optionally) activating the IRF port configuration.

        Args:
            member_id (string): The member ID of the switch.
            old_p1 (list): REQUIRED - A list of current interfaces
                bound to IRF port 1.
            old_p2 (list): REQUIRED - A list of current interfaces
                bound to IRF port 2.
            irf_p1 (list): REQUIRED - A list of desired interfaces to
                be bound to IRF port 1.
            irf_p2 (list): REQUIRED - A list of desired interfaces to
                be bound to IRF port 2.
            filename (str): OPTIONAL - The filename in which to
                save the current configuration.
                Defaults to 'startup.cfg'.
            activate (bool): OPTIONAL - Whether to immediately
                apply the IRF port configuration.
                Defaults to ``True``.

        Note:
            The ``irf_p1`` and ``irf_p2`` should be the complete physical
            interface list for IRF port 1 and IRF port 2, respectively.
            Interfaces not in the list will be removed.

        Note:
            If ``old_p1`` and ``old_p2`` are not accurate, behavior is
            undefined. These values can be obtained from ``get_config()``.

        Returns:
            A string representation of the list of
            staged configurations on the device.
        """
        if irf_p2 is None:
            irf_p2 = []
        if irf_p1 is None:
            irf_p1 = []
        if old_p2 is None:
            old_p2 = []
        if old_p1 is None:
            old_p1 = []
        updown_ifaces = []
        updown_ifaces += list(set(old_p1).difference(irf_p1))
        updown_ifaces += list(set(irf_p1).difference(old_p1))
        updown_ifaces += list(set(old_p2).difference(irf_p2))
        updown_ifaces += list(set(irf_p2).difference(old_p2))

        self._build_iface_updown(updown_ifaces, 'down')

        EN = nc_element_maker()
        EC = config_element_maker()

        operation1 = None
        if not irf_p1:
            operation1 = 'remove'

        iface1_eles = []
        for iface_name in irf_p1:
            iface1_eles.append(EC.Interface(EC.IfName(iface_name)))

        operation2 = None
        if not irf_p2:
            operation2 = 'remove'

        iface2_eles = []
        for iface_name in irf_p2:
            iface2_eles.append(EC.Interface(EC.IfName(iface_name)))

        config = EN.config(
            EC.top(
                EC.IRF(
                    EC.IRFPorts(
                        EC.IRFPort(
                            EC.MemberID(member_id),
                            EC.Port('1'),
                            *iface1_eles,
                            **operation_kwarg(operation1)
                        ),
                        EC.IRFPort(
                            EC.MemberID(member_id),
                            EC.Port('2'),
                            *iface2_eles,
                            **operation_kwarg(operation2)
                        ),
                    )
                )
            )
        )

        self.device.stage_config(config, 'edit_config')
        self._build_iface_updown(irf_p1 + irf_p2, 'up')

        self.device.stage_config(filename, 'save')

        if activate:
            EA = action_element_maker()
            top = EA.top(
                EA.IRF(
                    EA.PortConfiguration(
                        EA.Activate()
                    )
                )
            )

            self.device.stage_config(top, 'action')

        return self.device.staged_to_string()

    def get_config(self):
        """Get the current configuration of IRF ports on the device.

        Returns:
            A dictionary of IRF port bindings.

            It has the following format::

                {
                    <member_id>: {
                        'irf_p1' : <iface_list>,
                        'irf_p2' : <iface_list>
                    }
                }
        """
        irf_ports = {}

        E = data_element_maker()
        top = E.top(
            E.IRF(
                E.IRFPorts(
                    E.IRFPort(
                        E.Interface()
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        port_elems = findall_in_data('IRFPort', nc_get_reply)

        for port_ele in port_elems:
            iface_elems = findall_in_data('Interface', port_ele)
            port_num = find_in_data('Port', port_ele).text
            member_num = find_in_data('MemberID', port_ele).text

            if irf_ports.get(member_num) is None:
                irf_ports[member_num] = {}

            member_dict = irf_ports[member_num]
            if len(iface_elems):
                for iface_ele in iface_elems:
                    iface_name = find_in_data('IfName', iface_ele).text

                    if port_num == '1':
                        if member_dict.get('irf_p1') is None:
                            member_dict['irf_p1'] = []
                        irf_ports[member_num]['irf_p1'].append(iface_name)
                    elif port_num == '2':
                        if member_dict.get('irf_p2') is None:
                            member_dict['irf_p2'] = []
                        irf_ports[member_num]['irf_p2'].append(iface_name)

        return irf_ports


class IrfMember(object):
    """This class is used to get and build IRF port configurations
    on a ``COM7`` device.

    Args:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.

    Attributes:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
    """
    def __init__(self, device):
        self.device = device

    def _get_member_config(self, member_id):
        """Get membership configuration for the specified member ID.
        Information includes priority, description, and the new member ID.
        """
        irf_members = {}
        key_map = {'new_member_id': 'NewMemberID',
                   'descr': 'Description',
                   'priority': 'Priority'}

        E = data_element_maker()
        top = E.top(
            E.IRF(
                E.Members(
                    E.Member()
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        member_eles = findall_in_data('Member', nc_get_reply)

        for member_ele in member_eles:
            member_num = find_in_data('MemberID', member_ele).text
            irf_members[member_num] = data_elem_to_dict(member_ele, key_map)

        return irf_members.get(member_id)

    def _build_member_config(self, **params):
        """Build the IRF membership configuration.
        Configuration parameters include priority,
        description, and the new member id.

        Possible parameters:
            member_id (str)
            new_member_id (str)
            priority (str)
            descr (str)

        Returns:
            True is successful.
        """
        member_id = params.get('member_id')
        descr = params.get('descr')
        if descr:
            if not self.device.stage_config(
                    'irf member {0} description {1}'.format(
                        member_id, descr), 'cli_config'):
                return False

        new_member_id = params.get('new_member_id')
        if new_member_id:
            if not self.device.stage_config(
                    'irf member {0} renumber {1}'.format(
                        member_id, new_member_id), 'cli_config'):
                return False

        priority = params.get('priority')
        if priority:
            if not self.device.stage_config(
                    'irf member {0} priority {1}'.format(
                        member_id, priority), 'cli_config'):
                return False

        return True

    def _get_domain_config(self):
        """Return the domain id of switch or IRF stack.

        Returns:
            The domain id for the switch or IRF stack.
        """
        key_map = {'domain_id': 'Domain'}

        E = data_element_maker()
        top = E.top(
            E.IRF(
                E.Configuration()
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Configuration', nc_get_reply)

        domain_data = data_elem_to_dict(reply_data, key_map)

        return domain_data

    def _get_auto_update_config(self):
        """Return whether the IRF auto update feature is enabled.

        Returns:
            'enable' or 'disable'
        """
        key_map = {'auto_update': 'AutoUpgrade'}

        E = data_element_maker()
        top = E.top(
            E.IRF(
                E.Configuration()
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        reply_data = find_in_data('Configuration', nc_get_reply)

        au_data = data_elem_to_dict(reply_data, key_map)

        return au_data

    def _build_auto_update_domain_config(self, auto_update, domain_id):
        """Build the auto update config iformation.

        Args:
            auto_update (str): 'enable' or 'disable'
            domain_id (str): The domain id for the switch

        Returns:
            The staged config.
        """
        EN = nc_element_maker()
        EC = config_element_maker()

        data_eles = []
        if auto_update:
            data_eles.append(EC.AutoUpgrade(auto_update))

        if domain_id:
            data_eles.append(EC.Domain(domain_id))

        config = EN.config(
            EC.top(
                EC.IRF(
                    EC.Configuration(*data_eles)
                )
            )
        )

        return self.device.stage_config(config, 'edit_config')

    def _get_mad_exclude(self):
        """Get the currently configured mad excluded interfaces

        Returns:
            A dictionary::
                {
                    'mad_exclude': <interface list>
                }
        """
        mad_ex_ifaces = []
        raw_rsp = self.device.cli_display(
            'display current | inc "mad exclude interface"')
        lines = raw_rsp.split('\n')[1:-1]

        for line in lines:
            mad_ex_ifaces.append(line.split()[-1])

        return {'mad_exclude': mad_ex_ifaces}

    def _build_mad_exclude(self, iface_list):
        """Build the configuration for adding interfaces
        to the mad exclude list.
        """
        for iface_name in iface_list:
            iface = Interface(self.device, iface_name)
            if not iface.iface_exists:
                raise InterfaceAbsentError(iface.interface_name)
            if not self.device.stage_config(
                    'mad exclude interface {0}'.format(
                        iface.interface_name), 'cli_config'):
                return False
        return True

    def get_config(self, member_id):
        """Return the entire IRF membership configuration
        for a given member ID.

        Args:
            member_id (str): A current IRF member ID for
                the device.

        Returns:
            A dictionary with IRF membership configuration parameters.
            Including:
                :auto_update (str): 'enable' or 'disable'.
                mad_exclude (list): A list of interfaces
                    to be excluded from MAD mechanisms.
                new_member_id (str): The new IRF member
                    ID of the device to applied after reboot.
                descr (str): A textual description of the IRF member.
                priority (str): The priority of the IRF member.
                domain_id (str): The domain id of the member.

        Raises:
            IRFMemberDoesntExistError: if the IRF member doesn't exist.
        """
        member_config = self._get_member_config(member_id)
        if member_config is None:
            raise IRFMemberDoesntExistError(member_id)
        au_config = self._get_auto_update_config()
        madex_config = self._get_mad_exclude()
        domain_config = self._get_domain_config()

        member_config.update(au_config)
        member_config.update(madex_config)
        member_config.update(domain_config)

        return member_config

    def build(self, **params):
        """Build the IRF membership configuration.

        Args:
            **params: See Keyword Args.

        Keyword Args:
            auto_update (str): OPTIONAL - Enables or disables
                the auto-upgrade of software after an IRF
                convergence. Should be 'enable' or 'disable'.
            mad_exclude (list): OPTIONAL - A list of interfaces
                to be excluded from MAD mechanisms.
            member_id (str): REQUIRED - The current IRF member ID
                of the device.
            new_member_id (str) REQUIRED - The desired new IRF member
                ID of the device.
            domain_id (str) OPTIONAL - The domain id for the IRF member
            descr (str): OPTIONAL - A textual description of the IRF member.
            priority (str): OPTIONAL - The desired priority of the IRF member.

        Returns:
            True if successful, False otherwise.
        """
        if not self._build_member_config(**params):
            return False

        auto_update = params.get('auto_update')
        domain_id = params.get('domain_id')
        if auto_update or domain_id:
            if not self._build_auto_update_domain_config(auto_update, domain_id):
                return False

        mad_exclude = params.get('mad_exclude')
        if mad_exclude:
            if not self._build_mad_exclude(mad_exclude):
                return False

        return True

    def remove_mad_exclude(self, iface_list):
        """Stage the configuration to remove interfaces
        from the mad excluded list.
        """
        for iface_name in iface_list:
            self.device.stage_config(
                'undo mad exclude interface {0}'.format(
                    iface_name), 'cli_config')
