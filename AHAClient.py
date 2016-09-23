import requests
import xml.etree.ElementTree as ET
import hashlib
import sys


class AHAClient():
    def __init__(self, host, password):
        # to use https you have to configure your fritzbox https port
        # and use the certificate from the fritzbox
        self.host = "http://" + host
        self.password = password
        self.SID = self.login()
        self.devices_ain = None
        self.devices_name = None

    def login(self):
        response = requests.get(self.host+"/login_sid.lua")
        # print(response.status_code, response.text)
        if response.status_code != 200:
            print("Error @ plain request to login_sid.lua", response.status_code)
            sys.exit()
        root = ET.fromstring(response.text)
        SID = root.find('SID').text
        if SID == "0000000000000000":
            challenge = root.find('Challenge').text
            challenge_bf = (challenge + '-' + self.password).encode('utf-16le')
            m = hashlib.md5()
            m.update(challenge_bf)
            response_bf = challenge + '-' + m.hexdigest().lower()
        else:
            print("got a valid (already existing sid) sid")
            self.SID = SID
            return SID

        response = requests.get(self.host+"/login_sid.lua?&response=" + response_bf)

        if response.status_code != 200:
            print("{}  {}".format(response.status_code, response.text))
            sys.exit(0)
        else:
            # print("{}  {}".format(response.status_code, response.text))
            root = ET.fromstring(response.text)
            SID = root.find('SID').text
            if SID == "0000000000000000":
                print("ERROR invalid password")
                sys.exit()
            else:
                print("got a new session id")
                self.SID = SID
                return SID

    def homeautoswitch(self, ain=None, switchcmd=None, param=None):
        url_params = "?switchcmd=" + switchcmd + "&sid=" + self.SID
        if ain is not None:
            url_params += "&ain=" + ain
        if param is not None:
            url_params += "&param=" + param
        url = self.host + "/webservices/homeautoswitch.lua" + url_params
        response = requests.get(url)
        if response.status_code != 200:
            if response.status_code == 403:
                self.login()
                return self.homeautoswitch(ain=ain, switchcmd=switchcmd, param=param)
            print("Error")
            sys.exit()
        else:
            return response.text.strip()

    def get_name(self, ain):
        return self.homeautoswitch(switchcmd="getswitchname", ain=ain)

    def get_temp(self, ain):
        return int(self.homeautoswitch(switchcmd="gettemperature", ain=ain)) / 10

    def get_deviceinfos(self):
        return self.homeautoswitch(switchcmd="getdevicelistinfos")

    def getswitchlist(self):
        return self.homeautoswitch(switchcmd="getswitchlist")

    def get_state(self, ain):
        return self.homeautoswitch(switchcmd="getswitchstate", ain=ain)

    def get_present(self, ain):
        return self.homeautoswitch(switchcmd="getswitchpresent", ain=ain)

    def get_power(self, ain):
        return self.homeautoswitch(switchcmd="getswitchpower", ain=ain)

    def get_energy(self, ain):
        return self.homeautoswitch(switchcmd="getswitchenergy", ain=ain)

    def set_toggle(self, ain):
        return self.homeautoswitch(switchcmd="getswitchtoggle", ain=ain)

    def set_on(self, ain):
        return self.homeautoswitch(switchcmd="getswitchon", ain=ain)

    def set_off(self, ain):
        return self.homeautoswitch(switchcmd="getswitchoff", ain=ain)

    def get_devices(self):
        mydevices_ain = {}
        mydevices_name = {}
        devices = self.getswitchlist().split(",")
        for ain in devices:
            status = {}
            name = self.get_name(ain)
            status["name"] = name
            status["present"] = self.get_present(ain)
            mydevices_ain[ain] = status
            mydevices_name[name] = ain
        self.devices_ain = mydevices_ain
        self.devices_name = mydevices_name


def main():
    myAHA = AHAClient(host="192.168.0.1", password="")

    devices = myAHA.homeautoswitch(switchcmd="getswitchlist").split(",")
    for ain in devices:
        print("Name: {}\tAIN: {}\ttemperature: {}°C".format(myAHA.get_name(ain), ain, myAHA.get_temp(ain)))


if __name__ == "__main__":
    main()
