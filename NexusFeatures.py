import NxosCall
import numpy as np
import VpcCheck

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

# Get the list of currently active features on the Nexus
def getFeatureList(url,user,password):
    enFeatures = []
    featureList=NxosCall.NxosAPI(url,NxosCall.NxosShow("show feature"),user,password)["ins_api"]["outputs"]["output"]["body"]["TABLE_cfcFeatureCtrlTable"]["ROW_cfcFeatureCtrlTable"]

    print("Currently Enabled Features:")
    for each in featureList:
        if each["cfcFeatureCtrlOpStatus2"][:2] == "en" and each["cfcFeatureCtrlInstanceNum2"] <= 1:
            if each["cfcFeatureCtrlName2"] == "vpc":
                VpcCheck.getVpc(url,user,password)
            else:    
                enFeatures.append(each["cfcFeatureCtrlName2"])
                print(each["cfcFeatureCtrlName2"])
    
    return enFeatures

# Activate currently disbaled NXOS features based on required list
def setFeatures(url,user,password,features):

    if type(features) == list or type(features) == tuple:
        featureList = getFeatureList(url,user,password)
    else:
        print("ERROR: Features must be a tupile or list")
        return
    
    reqFeat = np.setdiff1d(features,featureList).tolist()

    print(reqFeat)

    featCmd = ""
    if len(reqFeat) > 0:
        print("Enabling features: ")
        for item in reqFeat:
            print(item)
            if item == reqFeat[len(reqFeat) - 1]:
                featCmd = featCmd + "feature " + item
            else:
                featCmd = featCmd + "feature " + item + " ;"
    
        enable=NxosCall.NxosAPI(url,NxosCall.NxosConfig(featCmd),user,password)["ins_api"]["outputs"]["output"]
        print(enable)
        NxosCall.NxosResult(enable)
        
    return "Feature check complete."
