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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = '''
---
author: Ansible Networking Team (@ansible-network)
name: comware
short_description: Use comware cliconf to run command on H3C Comware platform
description:
  - This comware plugin provides low level abstraction apis for
    sending and receiving CLI commands from H3C Comware network devices.
'''

import re
import json

from itertools import chain

from ansible.module_utils._text import to_text
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'comware'
        reply = self.get('display version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'^H3C.+Version\s+(\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1).strip(',')

        match = re.search(r'H3C\s+(\S+)\s+uptime', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    @enable_mode
    def get_config(self, source='running', flags=None, format='text'):
        if source != "running":
            raise ValueError(
                "fetching configuration from %s is not supported" % source,
            )

        cmd = "display current-configuration"

        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, candidate=None, commit=True, replace=False, comment=None):
        for cmd in chain(['system-view'], to_list(candidate), ['quit']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline,
                                 check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
