"""Mange config files on COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os


class Config(object):
    """This class is used to activate a new running config in real-time.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        filename (str): absolute path to the file that will be compared
            and/or activated on the device.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        filename (str): absolute path to the file that will be compared
            and/or activated on the device.

    """
    def __init__(self, device, filename):
        self.device = device
        self.filename = filename
        self.basename = os.path.basename(self.filename)
        self._diff_response = ''
        self._switch_response = []
        self._original__diffs = []
        self._diffs = []

    def _get__diffs_from_switch(self):
        """Compare switch running config to desired new config file.
        """
        cmds = 'display diff current-configuration configfile {0}'.format(
            self.basename)

        # raw string output taken directly from the switch showing the diff
        self._diff_response = self.device.cli_display(cmds)

    def compare_config(self):
        """Compare new config file to the existing current running config

        Returns:
            This returns a tuple of two elements that are both lists.

            The first element has a summary of diffs (self._diffs) and
            the second element is the exact output from the 'display diff'
            command, but as a list (self._original__diffs).
        """
        self._diffs = []
        new_cfg = []
        current_cfg = []

        if not self._diff_response:
            self._get__diffs_from_switch()

        # same as _diff_response, but as a list with each line as an element
        self._original__diffs = self._diff_response.split('\n')

        for line in self._original__diffs:
            if line.strip().startswith('-') and '#' not in line:
                current_cfg.append(line.strip('-').strip())
            elif line.strip().startswith('+') and '#' not in line:
                new_cfg.append(line.strip('+').strip())

        commands_to_apply = set(new_cfg).difference(current_cfg)
        commands_to_remove = set(current_cfg).difference(new_cfg)

        # diffs is summary of exactly which lines are changing in
        # _original__diffs because _diffs from switch show everything
        for each in commands_to_apply:
            self._diffs.append('+' + each)

        for each in commands_to_remove:
            self._diffs.append('-' + each)

        return self._diffs, self._original__diffs

#    def activate_replacement_config(self):
#        """Activate replacement config on host device
#
#        This method immediately activates the new config
#        file to be the new running config and does not perform a backup
#        or new save as is done in ``build_config``.
#
#        """
#        try:
#            # CLI response from switch during activation.
#            self._switch_response =  self.device.rollback(self.basename)
#        except RPCError as err:
#            if str(err).strip() == 'Operation failed.':
#                raise InvalidConfigFile
#
#        time.sleep(.5)

    def build(self, stage=False):
        """Stage or execute configuration required to activate new config file.

        This method stores the existing running configuration
        as flash:/safety_file.cfg, loads the new config file,
        and then stores the newly loaded file to flash:/startup.cfg.

        Args:
            stage (bool): whether to stage the commands or execute
                immediately

        Returns:
            True if stage=True and staging is successful
            List of etree.Element XML responses if immediate execution
        """
        if stage:
            backup = self.device.stage_config('safety_file.cfg', "save")
            rollback = self.device.stage_config(self.basename, "rollback")
            save = self.device.stage_config('startup.cfg', "save")
            return backup and rollback and save
        else:
            responses = []
            responses.append(self.device.save('safety_file.cfg'))
            responses.append(self.device.rollback(self.basename))
            responses.append(self.device.save('startup.cfg'))
            return responses
