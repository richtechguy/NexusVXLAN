import NxosCall
import re

# ******************************************************
# **                                                  **
# **     This code was written by Rich Cordan aka     **
# ** RichTechGuy for the RichTechGuy YouTube Channel. **
# **                                                  **
# **                www.richtechguy.com               **
# **            richtechguy@richtechguy.com           **
# **                                                  **
# ****************************************************** 

#    CreateBGPoverlay.py configures iBGP for VXLAN on Cisco Nexus 9000 switches
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

def showBGP(url,user,passwd):
    bgpEnabled = False
    bgp=NxosCall.NxosAPI(url,NxosCall.NxosShow("show feature"),user,passwd)["ins_api"]["outputs"]["output"]["body"]["TABLE_cfcFeatureCtrlTable"]["ROW_cfcFeatureCtrlTable"]
    for row in bgp:
        if row["cfcFeatureCtrlName2"] == "bgp":
            if row["cfcFeatureCtrlOpStatus2"] == re.compile("^enabled"):
                bgpEnabled = True
    return bgpEnabled

def getMyNeighbors(url,user,passwd,switches):
    lldp=NxosCall.NxosAPI(url,NxosCall.NxosShow("show lldp neighbors"),user,passwd)["ins_api"]["outputs"]["output"]["body"]["TABLE_nbor"]["ROW_nbor"]
    connected = []
    if type(lldp) is dict:
        for item in switches:
            if lldp["chassis_id"] == item:
                connected.append(lldp["chassis_id"])
    else:
        for each in lldp:
            for item in switches:
                if each["chassis_id"] == item:
                    connected.append(each["chassis_id"])
    return connected


def setBGPoverlay(url,user,passwd,asNum,isLeaf,neighborList,hostname,switches):
    activateBGP = "router bgp " + asNum + " ; router-id " + neighborList[hostname] + " ; address-family ipv4 unicast"
    startBGP=NxosCall.NxosAPI(url,NxosCall.NxosConfig(activateBGP),user,passwd)["ins_api"]["outputs"]["output"]
    print(startBGP)
    NxosCall.NxosResult(startBGP)

    whoNeighbors = getMyNeighbors(url,user,passwd,switches)

    confBGP = "router bgp " + asNum

    if isLeaf:
        for each in whoNeighbors:
            makeNeighbor=confBGP + " ; neighbor " + neighborList[each] + " ; remote-as " + asNum + " ; update-source loopback0 ; address-family ipv4 unicast ; send-community both"
            BGPneighbor=NxosCall.NxosAPI(url,NxosCall.NxosConfig(makeNeighbor),user,passwd)["ins_api"]["outputs"]["output"]
            NxosCall.NxosResult(BGPneighbor)
    else:
        for each in whoNeighbors:
            addIPv4 = "address-family ipv4 unicast ; send-community both ; route-reflector-client"
            makeNeighbor=confBGP + " ; neighbor " + neighborList[each] + " ; remote-as " + asNum + " ; update-source loopback0 ; " + addIPv4
            BGPneighbor=NxosCall.NxosAPI(url,NxosCall.NxosConfig(makeNeighbor),user,passwd)["ins_api"]["outputs"]["output"]
            NxosCall.NxosResult(BGPneighbor)

    return "BGP Overlay successfully created on switch " + url

def SetBGPevpn(url,user,passwd,asNum,isLeaf,neighborList,switches):
    whoNeighbors = getMyNeighbors(url,user,passwd,switches)
    confBGP = "router bgp " + asNum 

    setL2vpn = confBGP + " ; address-family l2vpn evpn ; retain route-target all"
    addL2vpn = NxosCall.NxosAPI(url,NxosCall.NxosConfig(setL2vpn),user,passwd)["ins_api"]["outputs"]["output"]
    NxosCall.NxosResult(addL2vpn)

    if isLeaf:
        for each in whoNeighbors:
            evpnNeighbor = confBGP + " ; neighbor " + neighborList[each] + " ; address-family l2vpn evpn ; send-community both"
            bgpEVPN = NxosCall.NxosAPI(url,NxosCall.NxosConfig(evpnNeighbor),user,passwd)["ins_api"]["outputs"]["output"]
            NxosCall.NxosResult(bgpEVPN)
    else:
        for each in whoNeighbors:
            evpnNeighbor = confBGP + " ; neighbor " + neighborList[each] + " ; address-family l2vpn evpn ; send-community both ; route-reflector-client"
            bgpEVPN = NxosCall.NxosAPI(url,NxosCall.NxosConfig(evpnNeighbor),user,passwd)["ins_api"]["outputs"]["output"]
            NxosCall.NxosResult(bgpEVPN)

    return "BGP EVPN successfully added to switch " + url