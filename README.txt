This python script is written to deploy VXLAN across a Cisco Nexus 9000 series switch infrastructure.  The script is broken up into multiple files which are:

DeployVXLAN.py  <-- This is the main script which calls the other supporting scripts.
NxosCall.py
NexusFeatures.py
CreateUnderlay.py
CreateBGPoverlay.py
CreateMultiCast.py

A breif description of each script is below.

This script was built and tested on Python 3.9 and requires the following python libraries:

numpy
json
re
urllib3
requests


Prior to running the script, the Nexus switches need to have some initial configuration completed:

- Complete startup configuration of the switch and configure username & password
- Configure mgmt0 IP address (if not done during initial setup)
- Interfaces connecting between Spine & Leaf switches must be set to layer 3 and have IP addresses configured.
- Interswitch links must be enabled
- The nxapi feature must be enabled on each switch
- It is recommended to enable LLDP prior to running the script.  The script will enable it, but it may pull LLDP info before it's available.  Enabling the feature before running the script resolves the issue.

All files including the config file must be in the same directory folder.

Config file:
The script pulls variable information from a JSON config file.  A sample config file is provided in the github repository.
The config file consists of the following elements:

Switches: A list containing dictionaries with the properties of each switch.  Copy/paste to add switches as needed.

    "switches": [
        {
        "hostname":"LEAF-1",
        "url":"192.168.0.11",
        "user":"admin",
        "password":"Lpasswd123!",
        "leaf":true,
        "loopback0":"10.10.10.1",
        "loopback1":"10.1.100.1"
        },
        {
        "hostname":"SPINE-1",
        "url":"192.168.0.21",
        "user":"admin",
        "password":"Spasswd123!",
        "leaf":false,
        "loopback0":"10.10.10.10",
        "loopback1":"10.10.100.1"
        }
    ],

    Each switch element consists of the following:
    hostname: the switch hostname
    url: IP address of the mgmt0 interface on the switch
    user: username for the script to use when connecting with the switch
    password: password to acces the switch as the user in "username"
    leaf: a boolean value to set whether this switch is to be configuered as a leaf switch 
        true = leaf switch
        false = spine switch
    loopback0: the IP address to be configured as the loopback0 IP for OSPF & BGP
    loopback1: the ip address to be configured for the loopback1 interface
        Leaf switches: this ip is used to bind to the nve1 interface
        Spine switches: this ip is used for pim anycast rp address

OSPF: This is the information for the OSPF instance used for the underlay 

    "ospf": {
        "name":"UNDERLAY"
    }
    name: the name of the OSPF instance for the VXLAN underlay

BGP: This is the information for the BGP overlay configuration on the switches

    "bgp": {
        "aSystem":"65000"
    }
    aSystem: the autonomous system number for the iBGP instance in this VXLAN environment.
        It is recommended to use a private AS number (64512 - 65534)

PIM: This is the information for the PIM multicast used for VXLAN

    "pim": {
        "group":"239.0.0.0/24"
    }
    group: the multicast ip in CIDR notation used for PIM - each VLAN will be assigned an IP within this range

VLANS: A list containing dictionaries with information for the VLANs to associate to VXLAN VNIDs.  
    Copy/paste to add VLAN information as needed.

    "vlans": [
        {
            "id":"42",
            "vnid":"40042",
            "mcast":"0.0.0.0",
            "ip":"0.0.0.0/0"
        },
        {
            "id":"100",
            "vnid":"40100",
            "mcast":"239.0.0.10",
            "ip":"172.20.10.1/24"
        }
    ]
    There will need to be one VLAN created for an L3 VXLAN tunnel, it is identified by an all-zero mcast & IP address.
    id: the 802.1q VLAN tag id number
    vnid: the VXLAN VNID to associate the VLAN to
    mcast: the multicast IP address for this VLAN, this must be within the range of the IP set in the PIM section of the config file.
    ip: the IP address for the VLAN's switched virtual interfaces to be configured on each leaf switch

VXLAN: VXLAN specific information

    "vxlan": {
        "anycastMac":"0000.1111.2222"
    }
    anycastMac: Mac address used for VXLAN anycast gateway, can be entered in 3 ways
        Method 1: 0000.0000.0000
        Method 2: 00:00:00:00:00:00
        Method 3: 00-00-00-00-00-00

VRF: This is the information for creating the VRF handling VXLAN traffic

    "vrf": {
        "context":"vxlan",
        "vni":"40042"
    }
    context: the name of the VRF
    vni: this must match the VNI of the VLAN used for the L3 VXLAN tunnel created in the VLAN section.

RouteMap: The name of the route map for redistributing direct routes into BGP.

    "routeMap":"permitAll"

-----

Script Descriptions:

DeployVXLAN.py
    This is the main script and the script that is run to deploy VXLAN across the nexus switches.
    When you have a completed config file, initiate this script from the command prompt using your preferred python 3 environment.

NxosCall.py
    This script is used by all other scripts to interact with the Cisco Nexus 9000 switches.
    The 'nxapi' feature must be active on all Nexus 9000 switches being configured.
    There are 2 nxos api calls used by the script. The first is the show call to get information from the switch.  The second is the config call to push configuration to the switch.


NexusFeatures.py
    This script activates the features needed on the Nexus 9000 switches which are required for VXLAN.

CreateUnderlay.py
    This script depolys OSPF as the underlay protocol for VXLAN on the Nexus 9000 switches.

CreateBGPoverlay.py
    This script is used to push MP-BGP configuration onto the switches as the overlay protocol.  
    It is used to deploy unicast BGP for the initial overlay, then used again to deploy l2vpn evpn BGP to the switches.
    The spine switches are configured as route reflectors during the configuration.
    The VXLAN deployment in these scripts utilizes iBGP and is not set up to deploy in an eBGP configuration.

CreateMultiCast.py
    This script will deploy PIM sparse-mode to the switches and set up the spine switches as the Anycast-RP devices.