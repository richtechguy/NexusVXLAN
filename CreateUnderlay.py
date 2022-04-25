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

#    CreateUnderlay.py configures OSPF on Cisco Nexus 9000 switches for VXLAN deployment
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

# Check the NXOS Feature list for active OSPF
def showOSPF(url,user,passwd):
    ospfEnabled = False
    ospf=NxosCall.NxosAPI(url,NxosCall.NxosShow("show feature"),user,passwd)["ins_api"]["outputs"]["output"]["body"]["TABLE_cfcFeatureCtrlTable"]["ROW_cfcFeatureCtrlTable"]
    for row in ospf:
        if row["cfcFeatureCtrlName2"] == "ospf":
            if row["cfcFeatureCtrlOpStatus2"] == re.compile("^enabled"):
                ospfEnabled = True
    return ospfEnabled

# Get LLDP data from the switch and compare to list of hostnames, returns list of interfaces connected to remote VXLAN switches
def getSpineLeafInt(url,user,passwd,hostnames):
    lldp=NxosCall.NxosAPI(url,NxosCall.NxosShow("show lldp neighbors"),user,passwd)["ins_api"]["outputs"]["output"]["body"]["TABLE_nbor"]["ROW_nbor"]
  
    linkList = []
    if type(lldp) is dict:
        for item in hostnames:
            if lldp["chassis_id"] == item:
                linkList.append(lldp["l_port_id"])
    else:
        for each in lldp:
            for item in hostnames:
                if each["chassis_id"] == item:
                    linkList.append(each["l_port_id"])
    return linkList


# Configure OSPF on a switch
def setOSPFunderlay(url,user,passwd,lo0,ospfName,hostnames):

    # Regular expressions for IPv4 Addresses with and without CIDR subnet notation.
    ip = re.compile("^(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[0|1]?[0-9][0-9]?)){3}$")
    ipCIDR = re.compile("^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$")
    
    # Create Loopback0 interface for OSFP router ID.
    print("Loopback IP Address: ", lo0)
    #print(ip.match(lo1))
    #print(ipCIDR.match(lo1))
    if ip.match(lo0):
        lo0CIDR = lo0 + "/32"
        print("Setting Loopback0 IP Address to: ",lo0CIDR)
    elif ipCIDR.match(lo0):
        lo0CIDR = lo0
        lo0 = re.sub("(\/([0-9]|[1-2][0-9]|3[0-2]))?$", "", lo0)
        print("Setting Loopback0 IP Address to: ",lo0CIDR)
    else:
        print("ERROR: Loopback address must be an ip address. 'X.X.X.X' or 'X.X.X.X/X'")
        return None
    print("Creating Loopback interface.")
    setLo1Cmd = "interface loopback0 ; ip address " + lo0CIDR + " ; ip router ospf " + ospfName + " area 0.0.0.0 ; no shutdown"
    loop0=NxosCall.NxosAPI(url,NxosCall.NxosConfig(setLo1Cmd),user, passwd)["ins_api"]["outputs"]["output"]
    #print(loop0)
    NxosCall.NxosResult(loop0)

    # Create OSPF instance on the switch
    print("Creating OSPF Instance")
    newOSPF="router ospf " + ospfName + " ; router-id " + lo0
    instanceOSPF=NxosCall.NxosAPI(url,NxosCall.NxosConfig(newOSPF),user,passwd)["ins_api"]["outputs"]["output"]
    print(instanceOSPF)
    NxosCall.NxosResult(instanceOSPF)

    # Identify the interfaces to other VXLAN switches
    ospfInterfaces = getSpineLeafInt(url,user,passwd,hostnames)

    # Configure OSPF on interfaces connecting to other VXLAN switches
    for each in ospfInterfaces:
        print("Setting OSPF on interface " + each)
        confIntOSPF = "interface " + each + " ; no switchport ; ip router ospf " + ospfName + " area 0.0.0.0 ; ip ospf network point-to-point ; no shutdown"
        setInterface = NxosCall.NxosAPI(url,NxosCall.NxosConfig(confIntOSPF),user,passwd)["ins_api"]["outputs"]["output"]
        NxosCall.NxosResult(setInterface)

    return "OSPF Underlay created at switch, "  + url

