"""Factory default COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class CleanErase(object):
    """Factory default a Comware 7 switch.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
    """

    def __init__(self, device):
        self.device = device

    def build(self, stage=False, factory_default=False):
        """Build cmd list to factory default switch and immediately reboot.

        Args:
            factory_default (bool): determines if the switch will be
                reset to factory defaults.  It is a safety measure and
                must be set to for the factory default to take place.
            stage (bool): whether to stage the command for later execution,
                or execute immediately.
        Returns:
            True if stage=True and staging is successful.
            The output of restore command if stage=False
        """
        if factory_default:
            commands = ['restore factory-default']
            if stage:
                return self.device.stage_config(commands, 'cli_display')
            else:
                try:
                    return self.device.cli_display(commands)
                finally:
                    self.device.reboot()
