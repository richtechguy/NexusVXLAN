import requests
import json

# ******************************************************
# **                                                  **
# **     This code was written by Rich Cordan aka     **
# ** RichTechGuy for the RichTechGuy YouTube Channel. **
# **                                                  **
# **    Some code was created via the NXAPI from a    **
# **              Cisco Nexus 9000 switch.            **
# **                                                  **
# **                www.richtechguy.com               **
# **            richtechguy@richtechguy.com           **
# **                                                  **
# ****************************************************** 

#    NxosCall.py enables python programs to interact with Nexus 9000 switches
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

# Send command to Nexus Switch API and collect response data.
def NxosAPI(urlSwitch,pyld,user,passwd):
    
    myheaders={'content-type':'application/json'}
    sysData = requests.post(urlSwitch,data=json.dumps(pyld),headers=myheaders,auth=(user,passwd),verify=False).json()
    #print(sysData)
    return sysData

# Format payload data for NXOS API show command.
def NxosShow(showCmd):
    print("Sending command: ", showCmd)

    payload={
        "ins_api": {
            "version": "1.0",
            "type": "cli_show",
            "chunk": "0",
            "sid": "1",
            "input": showCmd,
            "output_format": "json"
        }
    }

    return payload

# Format payload data for NXOS API configuration command.
def NxosConfig(configCmd):

    cmdText = ""
    if type(configCmd) == list or type(configCmd) == tuple:
        for item in configCmd:
            print("Sending command: ", item)
            if configCmd[len(configCmd) - 1] == item:
                cmdText = cmdText + item
            else:
                cmdText = cmdText + item + "; "
    elif type(configCmd) == str:
        cmdText = configCmd
        print("Sending command: ", cmdText)
    else:
        print("Error: command can only be list, tuple, or string.")
        print("Commands not sent.")

    payload = {
        "ins_api": {
            "version": "1.0",
            "type": "cli_conf",
            "chunk": "0",
            "sid": "1",
            "input": cmdText,
            "output_format": "json",
            "rollback": "rollback-on-error"
            }
        }

    return payload

def NxosResult(apiReply):
    if type(apiReply) is dict:
        if apiReply["code"] == "200":
            print("Success")
        else:
            print("Error: Config Attempt Failed!")
            print("Code: ", apiReply["code"])
            print("Msg: ", apiReply["msg"])
    else:
        for response in apiReply:
            print(response)
            if response["code"] == "200":
                print("Success!")
            else:
                print("Error: Config Attempt Failed!")
                print("Code: ", response["code"])
                print("Msg: ", response["msg"])