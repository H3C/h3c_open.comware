#
# (c) 2017 Red Hat Inc.
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

DOCUMENTATION = """
author: Ansible Networking Team (@ansible-network)
name: comware
short_description: Use comware netconf plugin to run netconf commands on Juniper JUNOS
  platform
description:
- This comware plugin provides low level abstraction apis for sending and receiving
  netconf commands from Juniper JUNOS network devices.
version_added: 1.0.0
options:
  ncclient_device_handler:
    type: str
    default: h3c
    description:
    - Specifies the ncclient device handler name for Juniper comware network os. To
      identify the ncclient device handler name refer ncclient library documentation.
"""
import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_native
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *
from ansible_collections.ansible.netcommon.plugins.plugin_utils.netconf_base import (
    NetconfBase,
    ensure_ncclient,
)

try:
    from ncclient import manager
    from ncclient.operations import RPCError
    from ncclient.transport.errors import SSHUnknownHostError
    from ncclient.xml_ import new_ele, sub_ele, to_ele, to_xml

    HAS_NCCLIENT = True
except (
        ImportError,
        AttributeError,
):  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    HAS_NCCLIENT = False


class Netconf(NetconfBase):

    @ensure_ncclient
    def get_device_info(self):
        device_info = dict()
        device_info["network_os"] = "comware"
        return device_info

    def get_capabilities(self):
        result = dict()
        result["rpc"] = self.get_base_rpc() + [
            "lock",
            "unlock",
            "command",
            "reboot",
        ]

        result["network_api"] = "netconf"
        result["device_info"] = self.get_device_info()
        return json.dumps(result)

    @staticmethod
    @ensure_ncclient
    def guess_network_os(obj):
        """
        Guess the remote network os name
        :param obj: Netconf connection class object
        :return: Network OS name
        """
        try:
            m = manager.connect(
                host=obj._play_context.remote_addr,
                port=obj._play_context.port or 830,
                username=obj._play_context.remote_user,
                password=obj._play_context.password,
                key_filename=obj.key_filename,
                hostkey_verify=obj.get_option("host_key_checking"),
                look_for_keys=obj.get_option("look_for_keys"),
                allow_agent=obj._play_context.allow_agent,
                timeout=obj.get_option("persistent_connect_timeout"),
                # We need to pass in the path to the ssh_config file when guessing
                # the network_os so that a jumphost is correctly used if defined
                ssh_config=obj._ssh_config,
            )
        except SSHUnknownHostError as exc:
            raise AnsibleConnectionFailure(to_native(exc))

        guessed_os = None
        for c in m.server_capabilities:
            if re.search("h3c", c):
                guessed_os = "comware"

        m.close_session()
        return guessed_os

    def execute(self, run_cmd_func, args=[], kwargs={}):
        """Safely execute the supplied function with args and kwargs.
        Args:
            run_cmd_func(executable): Function to be run.
        Returns:
            The return value of the supplied function.
        Raises:
            NCError: if there is an error in the NETCONF protocol.
            NCTimeoutError: if a client-side timeout has occured.
            ConnectionClosedError: if the NETCONF session is closed.
        """

        rsp = run_cmd_func(*args, **kwargs)
        if hasattr(rsp, "data_xml"):
            data = rsp.data_xml
        elif hasattr(rsp, "xml"):
            data = rsp.xml
        else:
            data = rsp

        return data

    def edit_config(self, config, target='running'):
        """Send a NETCONF edit_config XML object to the device.
        Args:
            config: etree.Element sent to ncclient.manager.edit_config
            target: Name of configuration on the remote device. Defaults to 'running'
        Returns:
            The etree.Element returned from ncclient.manager.edit_config
        """
        rsp = self.execute(self.m.edit_config, kwargs=dict(target=target, config=config))
        return rsp

    def action(self, element):
        """Wrapper for ncclient.manger.action
        Args:
            element: xml text sent to ncclient.manager.action
        Returns:
            The xml text returned from ncclient.manager.action
        """
        rsp = self.execute(self.m.action, [element])
        return rsp

    def save(self, filename=None):
        """Wrapper for ncclient.manger.save
        Args:
            element: etree.Element sent to ncclient.manager.save
        Returns:
            The etree.Element returned from ncclient.manager.save
        """
        rsp = self.execute(self.m.save, [filename])
        return rsp

    def rollback(self, filename):
        """Wrapper for ncclient.manger.rollback
        Args:
            element: etree.Element sent to ncclient.manager.rollback
        Returns:
            The etree.Element returned from ncclient.manager.rollback
        """
        rsp = self.execute(self.m.rollback, [filename])
        return rsp

    def cli_display(self, command):
        """Immediately push display commands to the device and returns text.
        Args:
            command (list or string): display commands
        Returns:
            xml text CLI output
        """

        if isinstance(command, list):
            command = '\n'.join(command)
        elif isinstance(command, str):
            command = command
        CLI = "<CLI><Execution>%s</Execution></CLI>" % command
        rsp = self.execute(self.dispatch, [CLI])
        return rsp

    @ensure_ncclient
    def cli_config(self, command):
        """Immediately push config commands to the device and returns text.
        Args:
            command (list or string): config commands
        Returns:
            xml text CLI output
        """
        if isinstance(command, list):
            command = '\n'.join(command)
        elif isinstance(command, str):
            command = command

        CLI = "<CLI><Configuration>%s</Configuration></CLI>" % command
        rsp = self.execute(self.dispatch, [CLI])
        return rsp

    def reboot_rspstr(self):
        """Attempt an rsp for reboot of the device.
        """

        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><rpc-reply></rpc-reply>"

    @ensure_ncclient
    def reboot(self):
        """Attempt an immediate reboot of the device.
        """
        try:
            self.m.async_mode = True
            self.cli_display(['reboot force'])
        except NCTimeoutError:
            pass
        except AttributeError:
            pass
        finally:
            self.m.async_mode = False

        rsp = self.reboot_rspstr()
        return rsp
