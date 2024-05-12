'''
main.py
Program entrypoint
ESC Viper Logging Suite
REQUIRED
A. Liebig for ESC
5/1/24
Version 1.5
'''
import json
import machine
import time

buttonPin = machine.Pin(0,machine.Pin.IN,machine.Pin.PULL_UP)

def buttonHandler(pin):
    print("button pushed")
    start_press = time.time()
    
    while buttonPin.value() == 0:
        pass
    
    time_pressed = time.time() - start_press
    
    
    if time_pressed > 1:
        machine.reset()
    #ledHandler(time_pressed)
    #_thread.start_new_thread(ledHandler,(time_pressed,))
    #if time_pressed < 5:
        
    #return time_pressed

buttonPin.irq(trigger = machine.Pin.IRQ_FALLING, handler = buttonHandler)

def ledHandler(octets):
    import neopixel
    ledPin = machine.Pin(15,machine.Pin.OUT)
    np = neopixel.NeoPixel(ledPin,8)
    #octetStrings = []
    print("octets: ")
    print(octets)
    for octet in octets:
        print("octet: ")
        print(octet)
        print(type(octet))
        #octetStrings.append(str(item))
        for char in octet:
            print("char: " + char)
            print(type(char))
            if int(char) < 9 and int(char) > 0:
                for i in range(int(char)):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(int(char)):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(int(char)):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(int(char)):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(int(char)):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(int(char)):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np.write()
                time.sleep(2)
            elif int(char) == 9:
                for i in range(7):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np[7] = (255,255,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(7):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np[7] = (0,0,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(7):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np[7] = (255,255,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(7):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np[7] = (0,0,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(7):
                    np[i] = (0,255,0)
                    time.sleep_ms(100)
                np[7] = (255,255,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                for i in range(7):
                    np[i] = (0,0,0)
                    time.sleep_ms(100)
                np[7] = (0,0,0)
                time.sleep_ms(100)
                np.write()
                time.sleep(2)
            elif int(char) == 0:
                np[0] = (255, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                np[0] = (0, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                np[0] = (255, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                np[0] = (0, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                np[0] = (255, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(1)
                np[0] = (0, 0, 0)
                time.sleep_ms(100)
                np.write()
                time.sleep(2) 
        time.sleep(3)
    #_thread.exit()
    
def displayIP():
    octets = station.ifconfig()[0].split(".")
    #_thread.start_new_thread(ledHandler,(octets))
    ledHandler(octets)


with open("config.json", 'r') as f:
    config = json.load(f)

if config["LAUNCHREPL"]:
    config["LAUNCHREPL"] = False
    with open("config.json",'w') as f:
        json.dump(config, f)
    
    #connect to wifi
    import network
    import webrepl
    
    station = network.WLAN(network.STA_IF)
    station.active(True)
    
    
    while not station.isconnected():
        station.connect(config["SSID"], config["WIPASS"])
        time.sleep(5)
    
    
    print(station.ifconfig()[0])
    #open a VPN connection so that webREPL will be local to azure network
    debugShell = webrepl.Webrepl()
    debugShell.start("escadmin")
    
    while not debugShell.connected:
        displayIP()
        time.sleep(5)
    
        
elif config["FACTORYRESETFLAG"]:
    config["FACTORYRESETFLAG"] = False
    with open("config.json",'w') as f:
        json.dump(config,f)
    #import setup
    
else:
    import logger
