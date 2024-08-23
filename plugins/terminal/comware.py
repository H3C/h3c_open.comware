#
# (c) 2016 Red Hat Inc.
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

import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common.text.converters import to_bytes
from ansible_collections.ansible.netcommon.plugins.plugin_utils.terminal_base import TerminalBase


class TerminalModule(TerminalBase):
    terminal_stdout_re = [
        re.compile(
            to_bytes(r"({primary:node\d+})?[\r\n]?[\w@+\-\.:\/\[\]]+[>#%] ?$"),
        ),
    ]

    terminal_stderr_re = [
        re.compile(to_bytes(r"unknown command")),
        re.compile(to_bytes(r"syntax error")),
        re.compile(to_bytes(r"[\r\n]error:")),
    ]

    terminal_config_prompt = re.compile(r"^.+#$")

    def on_open_shell(self):
        try:
            self._exec_cli_command(b"screen-length disable")
        except AnsibleConnectionFailure:
            raise AnsibleConnectionFailure("unable to set terminal parameters")
