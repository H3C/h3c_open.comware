"""Install an operating system on COM7 devices.
"""

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *


class SetStartup(object):
    """This class is used to get and build the startup file.
    It is often used in conjunction with ``set_startup.SetStartup``, which
    can operating the startup.

    Args:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.

    Attributes:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
    """

    def __init__(self, device):
        self.device = device

    def get_reboot_config(self):
        """Return a dictionary of current and startup image names.

        Returns:
            A dictionary of 'current', 'startup-primary', and
            'startup-backup' image file names. For each, there
            is a 'boot' image and a 'system' image::
                {
                    'current': {
                        'boot' : <current boot image>,
                        'system': <current system image>,
                    }
                    'startup-primary': {
                        'boot' : <primary startup boot image>,
                        'system': <primary startup system image>,
                    }
                    'startup-backup': {
                        'boot': <backup startup boot image>,
                        'system': <backup startup system image>
                    }
                }
        """
        E = data_element_maker()
        top = E.top(
            E.Package(
                E.BootLoaderList(
                    E.BootList()
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        boot_lists = findall_in_data('BootList', nc_get_reply)

        image_dict = {}

        key_map = {'0': 'current',
                   '1': 'startup-primary',
                   '2': 'startup-backup'}
        for boot_list in boot_lists:
            list_num = boot_list.findtext(
                './/{0}{1}'.format(NCDATA_C, 'BootType'))
            image_iter = boot_list.iterfind(
                './/{0}{1}'.format(NCDATA_C, 'FileName'))
            test = sum(1 for _ in image_iter)
            image_iter = boot_list.iterfind(
                './/{0}{1}'.format(NCDATA_C, 'FileName'))
            patch_file = ''
            if test <= 2:
                try:
                    boot_file = next(image_iter).text
                    sys_file = next(image_iter).text
                except StopIteration:
                    continue
            else:
                try:
                    boot_file = next(image_iter).text
                    sys_file = next(image_iter).text
                    patch_file = next(image_iter).text
                except StopIteration:
                    continue
            list_type = key_map[list_num]
            image_dict[list_type] = {}
            image_dict[list_type]['boot'] = boot_file.split(':/')[1]
            image_dict[list_type]['system'] = sys_file.split(':/')[1]
            if patch_file:
                image_dict[list_type]['patch'] = patch_file.split(':/')[1]
            else:
                image_dict[list_type]['patch'] = patch_file
        return image_dict

    def build(self, os_type, ipe=None, boot=None, system=None, patch=None,
              delete_ipe=False, stage=False):
        """Stage or execute the configuration commands
        for changing the primary startup image.

        Args:

        Returns:
            True if stage=True and successfully staged
            etree.Element XML response if immediate execution
        """
        E = action_element_maker()

        ipe_params = []
        boot_sys_params = []
        commands = []
        if patch:
            if os_type == 'ipe':
                cmd = 'boot-loader file {0} patch {1} all main'.format(ipe, patch)
                commands.append(cmd)
                commands.append('y\ny\ny\n')
            elif os_type == 'bootsys':
                cmd = 'boot-loader file boot {0} system {1} patch {2} all main'.format(boot, system, patch)
                commands.append(cmd)
                commands.append('y')
            if stage:
                return self.device.stage_config(commands, 'cli_display')
            else:
                return self.device.cli_display(commands)
        else:
            top = None
            if os_type == 'ipe':
                ipe_params.append(E.IPEFileName(ipe))
                ipe_params.append(E.DeleteIPEFile(str(delete_ipe).lower()))
                top = E.top(
                    E.Package(
                        E.SetBootImage(
                            E.Type('1'),
                            E.OverwriteLocalFile('false'),
                            *ipe_params
                        )
                    )
                )
            elif os_type == 'bootsys':
                boot_sys_ele = E.ImageFiles(
                    E.Boot(boot),
                    E.System(system)
                )
                boot_sys_params.append(boot_sys_ele)

                top = E.top(
                    E.Package(
                        E.SetBootImage(
                            E.Type('1'),
                            E.OverwriteLocalFile('false'),
                            *boot_sys_params
                        )
                    )
                )

            if stage:
                return self.device.stage_config(top, 'action')
            else:
                return self.device.action(top)
