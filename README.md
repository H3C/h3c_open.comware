# H3C OPEN comware Collection

[![CI](https://zuul-ci.org/gated.svg)](https://dashboard.zuul.ansible.com/t/ansible/project/github.com/ansible-collections/h3c_open.comware) <!--[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/vyos)](https://codecov.io/gh/ansible-collections/h3c_open.comware)-->
[![Codecov](https://codecov.io/gh/ansible-collections/h3c_open.comware/branch/main/graph/badge.svg)](https://codecov.io/gh/ansible-collections/h3c_open.comware)
[![CI](https://github.com/ansible-collections/h3c_open.comware/actions/workflows/tests.yml/badge.svg?branch=main&event=schedule)](https://github.com/ansible-collections/h3c_open.comware/actions/workflows/tests.yml)

The Ansible H3C OPEN comware collection includes a variety of Ansible content to help automate the management of H3C comware network appliances.

This collection has been tested against H3C Networks comware OS V7.

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.14.0**.

For collections that support Ansible 2.9, please ensure you update your `network_os` to use the
fully qualified collection name (for example, `h3c_open.comware.comware`).
Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

### Supported connections

The H3C OPEN comware collection supports `network_cli` and `netconf` connections.

## Included content

<!--start collection content-->
### Cliconf plugins
Name | Description
--- | ---
[h3c_open.comware.comware](https://github.com/ansible-collections/h3c_open.comware/blob/main/docs/h3c_open.comware.comware_cliconf.rst)|Use comware cliconf to run command on H3C comware OS platform

### Netconf plugins
Name | Description
--- | ---
[h3c_open.comware.comware](https://github.com/ansible-collections/h3c_open.comware/blob/main/docs/h3c_open.comware.comware_netconf.rst)|Use comware netconf plugin to run netconf commands on H3C comware platform

### Modules
Name | Description
--- | ---
h3c_open.comware.comware_snmp_group|Manages SNMP group configuration on H3C switches.
h3c_open.comware.comware_igmp|Configure the igmp issue to be applied to the interface.
h3c_open.comware.comware_snmp_target_host|Manages SNMP user configuration on H3c switches.
h3c_open.comware.comware_bgp_group|create and config bgp group
h3c_open.comware.comware_ping|Ping remote destinations *from* the Comware 7 switch
h3c_open.comware.comware_isis_interface|Manage isis for Comware 7 devices
h3c_open.comware.comware_bgp_global|config bgp configs in the bgp instance view such as routerid
h3c_open.comware.comware_startup|config the next restart file or ipe . patch function not available,please use patch module
h3c_open.comware.comware_intfstate|Check the port status. If there are undo shutdown ports but the field ports are down, list these inconsistent ports. If not, return OK.
h3c_open.comware.comware_rollback|Rollback the running configuration
h3c_open.comware.comware_ntp|Configure the ntp issue to be applied to the device.
h3c_open.comware.comware_vsi_intf|Configure some functions of vsi-interface
h3c_open.comware.comware_dldp|Manage dldp authentication,interface,timeout and mode on Comware 7 devices.
h3c_open.comware.comware_loghost|Manage info-center log host and related parameters on V7 devices
h3c_open.comware.comware_telemetryflowtrace|Manage Package information of the message sent to the collector on V7 devices
h3c_open.comware.comware_irf_ports|Manage IRF port creation and removal for Comware v7 devices
h3c_open.comware.comware_facts|Gather facts of Comware 7 devices
h3c_open.comware.comware_config|Back uo current configuration to the specified file
h3c_open.comware.comware_teleflowgroup_global|Manage telemetry flow group agingtime on Comware 7 devices.The default value is Varies by device.
h3c_open.comware.comware_command|Execute CLI commands on Comware 7 devices
h3c_open.comware.comware_file_copy|Copy a local file to a remote Comware v7 device
h3c_open.comware.comware_vrrp_global|Manage VRRP global configuration mode
h3c_open.comware.comware_netstream|Manage ip netstream,rate,timeout, max_entry,vxlan udp-port,and interface enable and ip netstream aggregation destination-prefix enable, netstream statistics output message destination address and destination UDP port number configurationon Comware 7 devices
h3c_open.comware.comware_lacp|Manage lacp system priority, system mac on Comware 7 devices
h3c_open.comware.comware_patch|Manage patch
h3c_open.comware.comware_log_source|Manage output rules for log information on V7 devices
h3c_open.comware.comware_clean_erase|Factory default Comware 7 device
h3c_open.comware.comware_irf_members|Manage IRF membership configuration
h3c_open.comware.comware_isis_global|Manage isis for Comware 7 devices
h3c_open.comware.comware_bgp_af|Manage address family configs
h3c_open.comware.comware_license|loading device license
h3c_open.comware.comware_save|Save the running configuration
h3c_open.comware.comware_sflow|Manage sflow attributes for Comware 7 devices
h3c_open.comware.comware_stp|Manage stp global BPDU enable, working mode and tc-bpdu attack protection function.
h3c_open.comware.comware_reboot|Perform a reboot of a Comware 7 device
h3c_open.comware.comware_snmp_user|Manages SNMP user configuration on H3c switches.
h3c_open.comware.comware_ospf_intf|Manage ospf in interface
h3c_open.comware.comware_log|get the device diagnostic information and upload to file server
h3c_open.comware.comware_neighbors|Retrieve active LLDP neighbors (read-only)
h3c_open.comware.comware_ftp|Configure device FTP function.
h3c_open.comware.comware_tele_stream|Manage telemetry global enable(disable) and telemetry stream timestamp enable(disable) and device-id on Comware 7 devices.Before config device-id,the timestamp must be enable.
h3c_open.comware.comware_install_config|Activate a new current-running config in realtime
h3c_open.comware.comware_bfd|Management configuration bfd function
h3c_open.comware.comware_lldp_global|Manage global config state for LLDP.this funtion can be take effect only global and interface LLDP all open. The interface LLDP is open default.
h3c_open.comware.comware_vrrp|Manage VRRP configurations on a Comware v7 device
h3c_open.comware.comware_ospf|Manage ospf
h3c_open.comware.comware_netconf|Manage netconf log and xml function on Comware 7 devices.XML cfg not support enter xml view now,This is not normally done.
h3c_open.comware.comware_lldp|Manage lacp fast-Interval, tx-interval,hold-multplier on Comware 7 devices
h3c_open.comware.comware_vpn_instance|config instance rely ensure some instance configs can be set
h3c_open.comware.comware_install_os|Copy (if necessary) and install a new operating system on Comware v7 device
h3c_open.comware.comware_evpn|Configure the EVPN issue to be applied to the device.
h3c_open.comware.comware_mtu|Manage mtu and jumboframe of the interface
h3c_open.comware.comware_vxlan|Manage VXLAN to VSI mappings and Tunnel mappings to VXLAN
h3c_open.comware.comware_ipinterface|Manage IPv4/IPv6 addresses on interfaces
h3c_open.comware.comware_acl|Configure the acl issue to be applied to the interface.
h3c_open.comware.comware_iface_stp|Manage stp config in interface
h3c_open.comware.comware_syslog_global|Manage system log timestamps and terminal logging level on Comware 7 devices
h3c_open.comware.comware_switchport|Manage Layer 2 parameters on switchport interfaces
h3c_open.comware.comware_l2vpn_global|Manage global config state for L2VPN
h3c_open.comware.comware_hwtacacs|Manage hwtacacs scheme
h3c_open.comware.comware_snmp_community|Manages SNMP community configuration on H3C switches.
h3c_open.comware.comware_local_user|Manage local_user
h3c_open.comware.comware_vxlan_tunnel|Manage VXLAN tunnels on Comware 7 devices
h3c_open.comware.comware_radius|create radius scheme
h3c_open.comware.comware_aaa|This module provides AAA related management configuration and applications
h3c_open.comware.comware_compare|Enter the configuration command and compare it with the expected result.
h3c_open.comware.comware_vsi|Configure some command functions of vsi view
h3c_open.comware.comware_vlan|Manage VLAN attributes for Comware 7 devices
h3c_open.comware.comware_sflow_intf|Manage sflow interface flow collector and sampling_rate on Comware 7 devices.
h3c_open.comware.comware_vxlan_svc_instance|Manage mapping of an Ethernet Service to a VSI (VXLAN ID)
h3c_open.comware.comware_portchannel|Manage port-channel (LAG) on Comware 7 devices
h3c_open.comware.comware_interface|Manage administrative state and physical attributes of the interface
h3c_open.comware.comware_lldp_interface|Manage lldp enable on interfaces.The default state is enable.
<!--end collection content-->

Click the `Content` button to see the list of content included in this collection.

## Installing this collection

You can install the H3C Networks comware collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install h3c_open.comware

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: h3c_open.comware
```

## Using this collection

You can call modules by their Fully Qualified Collection Namespace (FQCN), such as `h3c_open.comware.comware_l2_interfaces`.
The following example task replaces configuration changes in the existing configuration on a H3C Networks comware network device, using the FQCN:

```yaml
---
- name: Basic Ethernet config
  h3c_open.comware.comware_interface: 
    name: FortyGigE1/0/5 
    admin: up 
    description: mydesc 
    duplex: auto 
    speed: 40000 
```

### See Also:

- [H3C comware Platform options](https://docs.ansible.com/ansible/latest/network/user_guide/platform_comware.html).
- [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more details.

## Contributing to this collection

We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [H3C Networks comware collection repository](https://github.com/ansible-collections/h3c_open.comware). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

You can also join us on:

- IRC - the `#ansible-network` [irc.libera.chat](https://libera.chat/) channel
- Slack - https://ansiblenetwork.slack.com

See the [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) for details on contributing to Ansible.

### Code of Conduct

This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release notes

Release notes are available [here](https://github.com/ansible-collections/h3c_open.comware/blob/main/CHANGELOG.rst).

## Roadmap

<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->

## More information

- [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
