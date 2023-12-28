"""Reboot COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    RebootDateError, RebootTimeError
)


class Reboot(object):
    """This class is used to reboot a COM7 switch.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    """
    def __init__(self, device):
        self.device = device

    def build(self, stage=False, **reboot):
        """Build command list to reboot the switch and send to staging

        Args:
            stage (bool): whether to stage the commands or execute
                immediately
            reboot: see Keyword Args

        Keyword Args:
            reboot (bool): REQUIRED - set to True to reboot (safety)
            time (str): OPTIONAL - must be in HH:MM format
            date (str): OPTIONAL - must be in MM/DD/YYYY format
            delay (str): OPTIONAL - number representing delay in minutes

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """

        reb2 = reboot.get('reboot')
        time = reboot.get('time')
        delay = reboot.get('delay')
        date = reboot.get('date')
        commands = None

        if reb2:
            if delay:
                commands = ['scheduler reboot delay {0}'.format(delay)]
            elif time:
                if date:
                    commands = ['scheduler reboot at {0} {1}'.format(time,
                                                                     date)]
                else:
                    commands = ['scheduler reboot at {0}'.format(time)]
            else:
                commands = ['reboot force']
                # will exit/fail, NETCONF connection will not be closed

        if stage:
            return self.device.stage_config(commands, 'cli_display')
        else:
            return self.device.cli_display(commands)

    @staticmethod
    def param_check(**reboot):
        """Param validation for time & date.

        Args:
            reboot: see Keyword Args

        Keyword Args:
            time (str): OPTIONAL - must be in HH:MM format
            date (str): OPTIONAL - must be in MM/DD/YYYY format

        """

        time = reboot.get('time')
        if time:
            if len(time) != 5 or ':' not in time:
                raise RebootTimeError
            time_hh_mm = time.split(':')
            if len(time_hh_mm) != 2:
                raise RebootTimeError
            mm = time_hh_mm[0]
            hh = time_hh_mm[1]
            if len(mm) != 2 or len(hh) != 2:
                raise RebootTimeError

        date = reboot.get('date')
        if date:
            if '/' not in date:
                raise RebootDateError
            mm_dd_yyyy = date.split('/')
            if len(mm_dd_yyyy) != 3:
                raise RebootDateError
            mm = mm_dd_yyyy[0]
            dd = mm_dd_yyyy[1]
            yyyy = mm_dd_yyyy[2]
            if len(mm) != 1 and len(mm) != 2:
                raise RebootDateError
            if len(dd) != 1 and len(dd) != 2:
                raise RebootDateError
            if len(yyyy) != 4:
                raise RebootDateError
