import NxosCall
from CreateUnderlay import getSpineLeafInt
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

#    CreateMulticast.py configures PIM for VXLAN on Cisco Nexus 9000 switches
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

def setMcastOverlay(url,user,passwd,leaf,pimInfo,ospfName,hostnames):
    
    # Regular expressions for IPv4 Addresses with and without CIDR subnet notation.
    ip = re.compile("^(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)){3}$")
    ipCIDR = re.compile("^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$")

    if ip.match(pimInfo["anycast"]):
        lo1CIDR = pimInfo["anycast"] + "/32"
        print("Setting Loopback1 IP Address to: ",lo1CIDR)
    elif ipCIDR.match(pimInfo["anycast"]):
        lo1CIDR = pimInfo["anycast"]
        pimInfo["anycast"] = re.sub("(\/([0-9]|[1-2][0-9]|3[0-2]))?$", "", pimInfo["anycast"])
        print("Setting Loopback1 IP Address to: ",lo1CIDR)
    else:
        print("ERROR: Loopback address must be an ip address. 'X.X.X.X' or 'X.X.X.X/X'")
        return None

    deployPIM = "ip pim rp-address " + pimInfo["anycast"] + " group-list " + pimInfo["group"]
    setPIM=NxosCall.NxosAPI(url,NxosCall.NxosConfig(deployPIM),user,passwd)["ins_api"]["outputs"]["output"]
    print(setPIM)
    NxosCall.NxosResult(setPIM)

    interfaces = getSpineLeafInt(url,user,passwd,hostnames)

    if leaf:
        for each in interfaces:
            pimInt = "interface " + each + " ; ip pim sparse-mode"
            setInt = NxosCall.NxosAPI(url,NxosCall.NxosConfig(pimInt),user,passwd)["ins_api"]["outputs"]["output"]
            print(setInt)
            NxosCall.NxosResult(setInt)
    else:
        lo1Settings = "ip address " + lo1CIDR + " ; ip router ospf " + ospfName + " area 0.0.0.0 ; ip pim sparse-mode"
        setLo1 = "interface loopback1 ; " + lo1Settings
        createLo1=NxosCall.NxosAPI(url,NxosCall.NxosConfig(setLo1),user,passwd)["ins_api"]["outputs"]["output"]
        print(createLo1)
        NxosCall.NxosResult(setPIM)

        for addr in pimInfo["rpAddress"]:
            setRP="ip pim anycast-rp " + pimInfo["anycast"] + " " + addr
            pimRP=NxosCall.NxosAPI(url,NxosCall.NxosConfig(setRP),user,passwd)["ins_api"]["outputs"]["output"]
            print(pimRP)
            NxosCall.NxosResult(pimRP)

        for each in interfaces:
            pimInt = "interface " + each + " ; ip pim sparse-mode"
            setInt = NxosCall.NxosAPI(url,NxosCall.NxosConfig(pimInt),user,passwd)["ins_api"]["outputs"]["output"]
            print(setInt)
            NxosCall.NxosResult(setInt)

    return "PIM multicast configured on switch, " + url
