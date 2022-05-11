import json, re, urllib3
from numpy import append
import NexusFeatures
import CreateUnderlay
import CreateBGPoverlay
import CreateMultiCast
import NxosCall

# ******************************************************
# **                                                  **
# **     This code was written by Rich Cordan aka     **
# ** RichTechGuy for the RichTechGuy YouTube Channel. **
# **                                                  **
# **                www.richtechguy.com               **
# **            richtechguy@richtechguy.com           **
# **                                                  **
# ****************************************************** 

#    DeployVXLAN.py deploys VXLAN to Cisco Nexus 9000 switches
#    Copyright (C) 2022  Rich Cordan

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Disable Self-Signed Cert warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Open the config.json file and load its contents for switch configuration.
with open('config.json') as json_file:
    confVars = json.load(json_file)

    # nxData is a list containing dictionaries.
    # Each dictionary contains the config parameters of the switch.
    nxData = confVars["switches"]

# Regular expressions for IPv4 Addresses with and without CIDR subnet notation.
ip = re.compile("^(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)){3}$")
ipCIDR = re.compile("^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$")

switchList = []
for switch in nxData:
    switchList.append(switch["hostname"]) 

ospfInst = confVars["ospf"]["name"]

# Create a dictionary of hostnames to loopback interface0 IPs
lo0Dict = {}
for switch in nxData:
    lo0Dict.update({switch["hostname"] : switch["loopback0"]})

bgpAs = confVars["bgp"]["aSystem"]

pimData = {"group":confVars["pim"]["group"]}
rpAddress = []
rpKey = "anycast"
for switch in nxData:
    if not switch["leaf"]:
        if not rpKey in pimData.keys():
            pimData.update({"anycast":switch["loopback1"]})
        rpAddress.append(switch["loopback0"])

pimData.update({"rpAddress":rpAddress})

# Tuple containing the NXOS Features needed for VXLAN Deployment
featureList = (
    "bgp",
    "interface-vlan",
    "lacp",
    "lldp",
    "nv overlay",
    "ospf",
    "pim",
    "vn-segment-vlan-based"
)

# Format the switch["url"] variable for API interaction
for switch in nxData:
    if not re.search("^https?://", switch["url"]):
        switch["url"] = "https://" + switch["url"]
    if not re.search("ins$", switch["url"]):
        if re.search("/$", switch["url"]):
            switch["url"] = switch["url"] + "ins"
        else:
            switch["url"] = switch["url"] + "/ins"

# Set the hostname on each switch
for switch in nxData:
    setHost=NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig("hostname " + switch["hostname"]),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
    if setHost["code"] == "200":
        print("Hostname ", switch["hostname"], "successfully set.")
    else:
        print("Error: Failed to set hostname on ", switch["hostname"])

    # Verify that the correct NXOS features are active.
    featureCheck = NexusFeatures.setFeatures(switch["url"],switch["user"],switch["password"],featureList)
    print(featureCheck)

    # Create the OSPF underlay
    underlay = CreateUnderlay.setOSPFunderlay(switch["url"],switch["user"],switch["password"],switch["loopback0"],ospfInst,switchList)

    print(underlay)

    # Create the BGP overlay
    overlay = CreateBGPoverlay.setBGPoverlay(switch["url"],switch["user"],switch["password"],bgpAs,switch["leaf"],lo0Dict,switch["hostname"],switchList)
    
    print(overlay)

    # Create Multicast overlay
    mcast = CreateMultiCast.setMcastOverlay(switch["url"],switch["user"],switch["password"],switch["leaf"],pimData,ospfInst,switchList)

    print(mcast)

    # Enable VXLAN on the switch
    enVxlan = "nv overlay evpn ; fabric forwarding anycast-gateway-mac " + confVars["vxlan"]["anycastMac"]
    # Create VLANs on the leaf switches
    if switch["leaf"]:
        enableVxlan = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(enVxlan),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        print(enableVxlan)
        NxosCall.NxosResult(enableVxlan)

        for each in confVars["vlans"]:
            if ipCIDR.match(each["ip"]):
                setVLAN = "vlan " + each["id"] + " ; vn-segment " + each["vnid"]
            else:
                print("VLAN IP Must include subnet information! Example: 192.168.0.1/24")
            makeVlans = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setVLAN),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
            NxosCall.NxosResult(makeVlans)

        # Create the VXLAN VRF (Current version of the code only supports single tenant)
        addFamIPv4uni = "address-family ipv4 unicast ; route-target both auto ; route-target both auto evpn"
        setVRF = "vrf context " + confVars["vrf"]["context"] + " ; vni " + confVars["vrf"]["vni"] + " ; rd auto ; " + addFamIPv4uni
        confVRF = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setVRF),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(confVRF)

        fabForward = "no ip redirects ; fabric forwarding mode anycast-gateway"

        # Create SVI for each VLAN
        for each in confVars["vlans"]:
            if each["ip"] == "0.0.0.0/0":
                setSVI = "interface vlan " + each["id"] + " ; no shutdown ; vrf member " + confVars["vrf"]["context"] + " ; ip forward"
            else:
                sviIP = " ; ip address " + each["ip"]
                setSVI = "interface vlan " + each["id"] + " ; no shutdown ; vrf member " + confVars["vrf"]["context"] + " ; " + fabForward + sviIP
            editSVI = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setSVI),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
            print(editSVI)
            NxosCall.NxosResult(editSVI)

        # Create NVE interface for the VXLAN Vrf
        setNVE = "interface nve1 ; no shutdown ; host-reachability protocol bgp ; source-interface loopback1"
        makeNVE = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setNVE),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(makeNVE)

        nveLoop = "interface loopback1 ; ip address " + switch["loopback1"] + "/32 ; ip router ospf " + ospfInst + " area 0.0.0.0 ; ip pim sparse-mode"
        setLoop1 = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(nveLoop),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(setLoop1)
    else:
        # Activate VXLAN on feature on spine switches
        enableVxlan = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig("nv overlay evpn"),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        print(enableVxlan)
        NxosCall.NxosResult(enableVxlan)

    # Establish MP-BGP with addition of L2VPN EVPN protocols to the BGP AS
    buildEVPN = CreateBGPoverlay.SetBGPevpn(switch["url"],switch["user"],switch["password"],bgpAs,switch["leaf"],lo0Dict,switchList)
    print(buildEVPN)

    # Create VTEPs by associating VNIDs to the NVE interface.
    if switch["leaf"]:
        for each in confVars["vlans"]:
            if each["mcast"] == "0.0.0.0":
                setVNI = "interface nve1 ;member vni " + each["vnid"] + " associate-vrf"
                addEVPN = False
            else:
                setVNI = "interface nve1 ;member vni " + each["vnid"] + " ;mcast-group " + each["mcast"]
                addEVPN = True
                setEVPN = "evpn ;vni " + each["vnid"] + " l2 ;rd auto ;route-target import auto ;route-target export auto"
            vniMcast = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setVNI),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
            print(vniMcast)
            NxosCall.NxosResult(vniMcast)
            if addEVPN:
                makeEVPN = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setEVPN),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
                print(makeEVPN)
                NxosCall.NxosResult(makeEVPN)

        # Redistribute direct routes into BGP
        setRouteMap = "route-map " + confVars["routeMap"] + " permit 10"
        makeRouteMap = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(setRouteMap),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(makeRouteMap)

        redisBGP = "router bgp " + bgpAs + " ;vrf " + confVars["vrf"]["context"] + " ;address-family ipv4 unicast ;redistribute direct route-map " + confVars["routeMap"]
        setRedisBGP = NxosCall.NxosAPI(switch["url"],NxosCall.NxosConfig(redisBGP),switch["user"],switch["password"])["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(setRedisBGP)

    print("VXLAN Configured on switch " + switch["hostname"] + ".")