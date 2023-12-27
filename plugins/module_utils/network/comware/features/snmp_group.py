"""Manage interfaces on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class SnmpGroup(object):
    """This class is used to get data and configure a specific snmp group.

    """

    def __init__(self, device, group_name=None, version=None, security_level=None):
        self.device = device
        if group_name:
            self.group_name = group_name
        if version:
            self.version = version
        if security_level:
            self.security_level = security_level

        # dictionary to XML tag mappings
        self.group_key_map = {
            'group_name': 'Name',
            'version': 'SecurityMode',
            'security_level': 'SecurityLevel',
            'read_view': 'ReadView',
            'write_view': 'WriteView',
            'notify_view': 'NotifyView'
        }

        self.R_group_key_map = dict(reversed(item) for item in self.group_key_map.items())
        self.value_map = {
            'SecurityLevel': {
                '1': 'NoAuthNoPriv',
                '2': 'authentication',
                '3': 'privacy'
            },
            'SecurityMode': {
                '1': 'v1',
                '2': 'v2c',
                '3': 'v3'
            }
        }
        self.R_value_map = reverse_value_map(
            self.R_group_key_map, self.value_map)

    @staticmethod
    def gen_top():
        E = data_element_maker()
        top = E.SNMP(
            E.Groups(
                E.Group(
                )
            )
        )

        return top

    def get_group_list(self):
        """Get a list of names that exist on the switch.

        Returns:
            It returns a list of names as strings.
        """
        top = self.gen_top()
        nc_get_reply = self.device.get(('subtree', top))
        group_xml = findall_in_data('Name', nc_get_reply)
        groups = [group.text for group in group_xml]

        return groups

    def get_config(self):
        """Gets current configuration for a given snmp group name
        """
        top = self.gen_top()
        group_comm_ele = find_in_data('Group', top)
        group_comm_ele.append(data_element_maker().Name(self.group_name))
        nc_get_reply = self.device.get(('subtree', top))
        snmp_group_config = data_elem_to_dict(nc_get_reply, self.group_key_map, value_map=self.value_map)
        return snmp_group_config

    def group_build(self, stage=True, **group):

        group['group_name'] = self.group_name
        group['version'] = self.version
        group['security_level'] = self.security_level
        group_name = group.get('group_name')
        version = group.get('version')
        security_level = group.get('security_level')
        acl_number = group.get('acl_number')
        read_view = group.get('read_view')
        write_view = group.get('write_view')
        notify_view = group.get('notify_view')
        commands = []
        if security_level == 'noAuthNoPriv':

            cmd = 'snmp-agent group {0} {1}'.format(version, group_name)
            if read_view:
                cmd = cmd + ' read-view {0}'.format(read_view)
            if notify_view:
                cmd = cmd + ' notify-view {0}'.format(notify_view)
            if write_view:
                cmd = cmd + ' write-view {0}'.format(write_view)
            if acl_number:
                cmd = cmd + ' acl {0}'.format(acl_number)
            commands.append(cmd)

        elif security_level != 'noAuthNoPriv' and version == 'v3':
            cmd = 'snmp-agent group {0} {1} {2}'.format(version, group_name, security_level)
            if read_view:
                cmd = cmd + ' read-view {0}'.format(read_view)
            if notify_view:
                cmd = cmd + ' notify-view {0}'.format(notify_view)
            if write_view:
                cmd = cmd + ' write-view {0}'.format(write_view)
            if acl_number:
                cmd = cmd + ' acl {0}'.format(acl_number)
            commands.append(cmd)

        if commands:
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)

    def group_remove(self, stage=True, **group):

        group['group_name'] = self.group_name
        group['version'] = self.version
        group['security_level'] = self.security_level
        group_name = group.get('group_name')
        version = group.get('version')
        security_level = group.get('security_level')

        commands = []
        if security_level == 'noAuthNoPriv' and version and group_name:
            cmd = 'undo snmp-agent group {0} {1}'.format(version, group_name)
            commands.append(cmd)
        elif security_level != 'noAuthNoPriv' and version == 'v3' and group_name:
            cmd = 'undo snmp-agent group {0} {1} {2}'.format(version, group_name, security_level)
            commands.append(cmd)

        if commands:
            if stage:
                return self.device.stage_config(commands, 'cli_config')
            else:
                return self.device.cli_config(commands)
