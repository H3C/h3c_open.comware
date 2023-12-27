#
# (c) 2017 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.netconf import (
    NetconfConnection,
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.namespaces import \
    NETCONFBASE_C

try:
    from lxml.etree import Element, SubElement
    from lxml.etree import tostring as xml_to_string

    HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Element, SubElement
    from xml.etree.ElementTree import tostring as xml_to_string

    HAS_LXML = False


def _strip_return(text):
    """Strip excess return characters from text.
    """
    if text:
        text = text.replace('\r\r\r', '\r')
        text = text.replace('\r\r', '\r')
        text = text.replace('\n\n\n', '\n')
        text = text.replace('\n\n', '\n')

    return text


class Device(object):
    """This class manages the NETCONF connection to an Comware switch,
    and provides methods to execute various NETCONF operations.

    """

    def __init__(self, module):
        self.staged = []
        self.module = module
        self.connection = get_connection(module)

    def stage_config(self, config, cfg_type):
        """Append config object to the staging area.

        Args:
            config: The config payload. Could be a partial etree.Element XML
                object or raw text if using a CLI config type
            cfg_type (string): The type of config payload.
                Permitted options: "edit_config", "action", "cli_config",
                "cli_display", "save", "rollback"

        Returns:
            True if config object was successfully staged.

        Raises:
            ValueError: if an invalid config type is supplied.
        """
        if cfg_type in ['edit_config', 'action', 'cli_config',
                        'cli_display', 'save', 'rollback']:
            self.staged.append({'config': config, 'cfg_type': cfg_type})
            return True
        else:
            raise ValueError("Invalid config type for staging.  Must be one"
                             + "of the following: edit_config, action, "
                             + "cli_config, cli_display, save, rollback")

    def staged_to_string(self):
        """Convert the staging area to a list of strings.

        Returns:
            A list of string representing the configuration in the
            staging area.
        """
        cfgs = []
        for cfg in self.staged:
            if (not isinstance(cfg['config'], str)) and (not isinstance(cfg['config'], list)):
                cfgs.append(xml_to_string(cfg['config'], encoding='unicode'))
            else:
                cfgs.append(cfg['config'])

        return cfgs

    def execute_staged(self, target='running'):
        """Execute/Push the XML object(s) or CLI strings in the staging
        area (self.staged) to the device.
        Args:
            target (str): must be set to running.
                It *could* change in the future
                if supports candidate configurations, etc.
                Only used for 'edit_config' API calls.
                Defaults to 'running'.
        Returns:
            A list of responses received from the device.
            Responses with CLI information are extracted from the XML
            response.
        """
        rsps = []
        for command in self.staged:
            cfg_type = command['cfg_type']
            config = command['config']
            args = []
            kwargs = {}
            if cfg_type == 'edit_config':
                run_cmd_func, kwargs = self.edit_config, dict(target=target, config=config)
            elif cfg_type == 'action':
                run_cmd_func, args = self.action, [config]
            elif cfg_type == 'save':
                run_cmd_func, args = self.save, [config]
            elif cfg_type == 'rollback':
                run_cmd_func, args = self.rollback, [config]
            elif cfg_type == 'cli_config':
                run_cmd_func, args = self.cli_config, [config]
            elif cfg_type == 'cli_display':
                run_cmd_func, args = self.cli_display, [config]
            else:
                continue
            rsps.append(run_cmd_func(*args, **kwargs))

        del self.staged[:]
        return rsps

    def edit_config(self, config, target='running'):
        """Send a NETCONF edit_config XML object to the device.
        Args:
            config: xml text sent to ncclient.manager.edit_config
            target: Name of configuration on the remote device. Defaults to 'running'
        Returns:
            The xml text returned from ncclient.manager.edit_config
        """
        xml_str = xml_to_string(config, encoding='unicode')
        rsp = self.connection.edit_config(xml_str, target)
        return rsp

    def get(self, get_tuple=None):
        rsp = None
        if get_tuple and len(get_tuple) == 2:
            get_list = list(get_tuple)
            get_list[1] = xml_to_string(get_list[1], encoding='unicode')
            rsp = self.connection.get(get_list)
        return rsp

    def action(self, element):
        xml_str = xml_to_string(element, encoding='unicode')
        rsp = self.connection.action(xml_str)
        return rsp

    def save(self, filename=None):
        rsp = None
        try:
            rsp = self.connection.save(filename)
        except ConnectionError as exc:
            self.module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
        return rsp

    def rollback(self, filename):
        rsp = None
        try:
            rsp = self.connection.rollback(filename)
        except ConnectionError as exc:
            self.module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
        return rsp

    def cli_display(self, command):
        rsp = self.connection.cli_display(command)
        return self._extract_config(rsp)

    def cli_config(self, command):
        """Immediately push config commands to the device and returns text.
        Args:
            command (list or string): config commands
        Returns:
            raw text CLI output
        """
        rsp = self.connection.cli_config(command)
        return self._extract_config(rsp)

    def reboot(self):
        """Attempt an immediate reboot of the device.

        """
        self.connection.reboot()


    @staticmethod
    def _extract_config(xml_resp):
        """Extract a CLI response from an XML object.
        """
        conf = xml_resp.find('.//{0}Configuration'.format(NETCONFBASE_C))
        execu = xml_resp.find('.//{0}Execution'.format(NETCONFBASE_C))

        if execu is not None:
            text = execu.text
        elif conf is not None:
            text = conf.text
        else:
            text = 'Unable to extract CLI data.'

        text = _strip_return(text)

        return text

    @staticmethod
    def _find_between(s, first, last):
        """Find a substring in between two other substrings.

        Args:
            s: The full string
            first: The first substring
            last: The second substring
        """
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""


def tostring(element, encoding="UTF-8", pretty_print=False):
    if HAS_LXML:
        return xml_to_string(
            element,
            encoding="unicode",
            pretty_print=pretty_print,
        )
    else:
        return to_text(
            xml_to_string(element, encoding),
            encoding=encoding,
        )


def get_connection(module):
    if hasattr(module, "_comware_connection"):
        return module._comware_connection
    capabilities = get_capabilities(module)
    network_api = capabilities.get("network_api")
    if network_api == "cliconf":
        module._comware_connection = Connection(module._socket_path)
    elif network_api == "netconf":
        module._comware_connection = NetconfConnection(module._socket_path)
    else:
        module.fail_json(msg="Invalid connection type %s" % network_api)

    return module._comware_connection


def get_capabilities(module):
    if hasattr(module, "_comware_capabilities"):
        return module._comware_capabilities
    capabilities = None
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))
    module._comware_capabilities = json.loads(capabilities)
    return module._comware_capabilities


def get_device(module):
    device = None
    try:
        device = Device(module)
    except ConnectionError as exc:
        module.fail_json("unable to get device %s" % (to_text(exc)))
    return device
