import NxosCall
import time

# ******************************************************
# **                                                  **
# **     This code was written by Rich Cordan aka     **
# ** RichTechGuy for the RichTechGuy YouTube Channel. **
# **                                                  **
# **                www.richtechguy.com               **
# **            richtechguy@richtechguy.com           **
# **                                                  **
# ****************************************************** 

#    NexusFeatures.py activates features on Cisco Nexus 9000 switches
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

def getVpc(url,user,password):
    vpcData = NxosCall.NxosAPI(url,NxosCall.NxosShow("show vpc"),user,password)["ins_api"]["outputs"]["output"]["body"]
    if vpcData["vpc-domain-id"] == "not configured":
        noVpc = killVpc(url,user,password)
    else:
        print("*** WARNING ***")
        print("vPC is configured on this switch.")
        print("After VXLAN is configuered, additional")
        print("vPC configuration is necessary!")
        print("Refer to Cisco NXOS VXLAN configuration")
        print("Documentation for vPC configuration on VXLAN.")
        print("***************")
        time.sleep(10)


def killVpc(url,user,password):
    vpcKill = NxosCall.NxosAPI(url,NxosCall.NxosConfig("no feature vpc"),user,password)["ins_api"]["outputs"]["output"]
    NxosCall.NxosResult(vpcKill)