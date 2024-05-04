'''
logger.py
Main Logging Loop
ESC Viper Logging Suite
REQUIRED
A. Liebig for ESC
5/2/24
Version 1.7
'''

import time
import json
import onewire
import ds18x20 #Temperature probe
import as7265x #Photospectrometer
import TSL2591 #Luminosity Sensor
import network
import socket
import ubinascii
import machine
import ugit #OTA Updater
import scd40 #Atmospheric CO2 Sensor
import gc
import struct
import bme280 #Atmospheric Sensor
import traceback
import os
import statistics
#import webrepl
from umqttsimple import MQTTClient
from ina219 import INA219 #current sensor

#load the configuration:
with open("config.json",'r') as f:
    config = json.load(f)

#TODO: remember to machine.reset after log interval change because otherwise watchdog timing will be wrong
#start the watchdog:
#memDog = machine.WDT(id=0, timeout=config["LOGINTERVAL"] * 5 * 1000)
#memDog.feed()

offlineMode = False
UID = ubinascii.hexlify(machine.unique_id())

telemTopic = config["TELEMTOPIC"].format(config["TENANT"],UID.decode())
ccTopic = config["CCTOPIC"].format(config["TENANT"],UID.decode())
logTopic = config["LOGTOPIC"].format(config["TENANT"],UID.decode())
statusTopic = config["STATUSTOPIC"].format(config["TENANT"],UID.decode())

print(telemTopic)

client = MQTTClient(ubinascii.hexlify(machine.unique_id()), config["BROKER"], keepalive=60)


#connect to wifi:
try:
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(config["SSID"], config["WIPASS"])
except Exception as error:
    #errorHandler("wifi setup", error, traceback.print_stack())
    print("wifi error")
time.sleep(1)

firstConAttempts = 0

while station.isconnected() == False:
    
    firstConAttempts += 1
    
    if firstConAttempts < 10:
        print("not connected")
        time.sleep(2)
        
    elif firstConAttempts == 10:
        print("having trouble connecting, waiting and trying again")
        time.sleep(15)
        
    elif firstConAttempts >= 20:
        print("can't make wifi connection, going to offline mode")
        offlineMode = True
        break

try:
    print(station.ifconfig())
except Exception as error:
    #errorHandler("IP error", error, traceback.print_stack())
    print(error)

#statusHandler("wifi connection", "connected successfully")

time.sleep(1)

#log exceptions and stack trace
def errorHandler(source, message, trace):
    with open("errorlog.txt",'a') as f:
        f.write("\nNew exception at " + str(rtClock.datetime()) + ": ")
        f.write("\n\tSource: " + source + "\n\tMessage: " + str(message) + "\n\tTrace: " + str(trace) + "\n")
        
    try:
        mem = gc.mem_free()
        logPayload = {
                        "Source": source,
                        "Message": message,
                        "Trace": trace,
                        "Mem": mem
                      }
        print(logPayload)
        client.publish(logTopic, json.dumps(logPayload).encode())
    except:
        print("error writing file, this is for debug")
        #with open("errorlog.txt",'a') as f:
            #f.write("\nCould not report error over MQTT at: " + str(rtClock.datetime()))

#log status events:
def statusHandler(source, message):
    mem = gc.mem_free()
    statusPayload = {
                        "Source": source,
                        "Message": message,
                        "Time": str(rtClock.datetime()),
                        "Mem": mem
                    }
    try:
        client.publish(statusTopic, json.dumps(statusPayload).encode())
    except Exception as error:
        print(error)
        errorHandler("status message publish", error, traceback.print_stack())
        #TODO: do something here, maybe just an additional note in local log


#setup the RTC
NTP_DELTA = 3155673600 + 25200   #Adjust this for time zone
timeHost = "pool.ntp.org"
rtClock = machine.RTC()

def set_time():
    # Get the external time reference
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(timeHost, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    except Exception as error:
        errorHandler("NTP error", error, traceback.print_stack())
        print("NTP error")
    finally:
        s.close()

    #Set our internal time
    val = struct.unpack("!I", msg[40:44])[0]
    tm = val - NTP_DELTA    
    t = time.gmtime(tm)
    rtClock.datetime((t[0],t[1],t[2],t[6]+1,t[3],t[4],t[5],0))

try:
    set_time()
except Exception as error:
    print(error)
    errorHandler("set rt clock", error, traceback.print_stack())
else:
    statusHandler("wifi setup", "initial wifi connection successful")


if config["LASTUPDATECHECK"] == 0: #or config["LASTUPDATECHECK"]
    config["LASTUPDATECHECK"] = time.mktime(rtClock.datetime())
else:
    pass

#lastUpdateCheck = config["LASTUPDATECHECK"]

#Instantiate MQTT client and define callbacks:
def sub_cb(topic, msg):
  global config
  global fanEnabled
  global fanOverride
  print((topic, msg))
  if topic.decode() == ccTopic:
    decodedMsg = json.loads(msg.decode())
    subject = decodedMsg.get("subject")
    #print('Topic: ' + topic + 'Message: ' + msg)
    if subject == "returnSettings":
        '''
        theSettings = {
            "loggingInterval": 25,
            "spectralGain": "16x"
            }
        '''
        print("send the config")
        client.publish(ccTopic, json.dumps(config).encode())

    elif subject == "changeSetting":
        try:
            if decodedMsg["SETTING"] in locals():
                if isinstance(decodedMsg["VALUE"],type(locals()[decodedMsg["SETTING"]])):
                    locals()[decodedMsg["SETTING"]] = decodedMsg["VALUE"]
                    print(str(decodedMsg["SETTING"]) + " changed to " + str(decodedMsg["VALUE"]))
                    try:
                        statusHandler("remote command", str(decodedMsg["SETTING"]) + " changed to " + str(decodedMsg["VALUE"]))
                    except:
                        pass
                else:
                    pass
                    #raise exception for no such setting/invalid value
            elif decodedMsg["SETTING"] in globals():
                if isinstance(decodedMsg["VALUE"],type(globals()[decodedMsg["SETTING"]])):
                    globals()[decodedMsg["SETTING"]] = decodedMsg["VALUE"]
                    print(str(decodedMsg["SETTING"]) + " changed to " + str(decodedMsg["VALUE"]))
                    try:
                        statusHandler("remote command", str(decodedMsg["SETTING"]) + " changed to " + str(decodedMsg["VALUE"]))
                    except:
                        pass
                else:
                    pass
                    #raise exception for no such setting/invalid value
            elif decodedMsg["SETTING"] in config.keys():
                with open("configBak.json",'w') as f:
                    json.dump(config,f)
                if isinstance(decodedMsg["VALUE"], type(config[decodedMsg["SETTING"]])):
                    config[decodedMsg["SETTING"]] = decodedMsg["VALUE"]
                    with open("config.json",'w') as f:
                        json.dump(config,f)
                else:
                    pass
                    #raise exception about data type
            else:
                #raise exception for setting not found
                pass    
        except Exception as error:
            print("parsing error: ")
            print(error)
    elif subject == "revertSettings":
        try:
            if "configBak.json" in os.listdir():
                os.remove("config.json")
                with open("configBak.json",'r') as f:
                    config = json.load(f)
                    
                with open("config.json",'w') as f:
                    json.dump(config,f)
            else:
                print("no backup config found")
        except Exception as error:
            print(error)
        
    elif subject == "checkForUpdate":
        try:
            print("call the updater")
            import ugit
            try:
                config["LASTUPDATECHECK"] = time.mktime(rtClock.datetime())
                with open("config.json", 'w') as f:
                    json.dump(config, f)
            except Exception as error:
                print(error)
            ugit.pull_all(isconnected = True)
            
        except Exception as error:
            errorHandler("updater pull all", error, traceback.print_stack())
    elif subject == "forceReboot":
        machine.reset()
    elif subject == "forceFileUpdate":
        print("manually update file: " + msg)
        try:
            import ugit
            ugit.pull(msg)
        except Exception as error:
            errorHandler("manual file update", error, traceback.print_stack())
        
    else:
        print('message recieved: ' + msg)
    
disconMsg = {
             "Source": "Last Will",
             "Message": "Client " + str(UID) + " has disconnected unexpectedly"
            }
'''    
try:    
    disconMsg = "Client " + str(UID) + " has disconnected unexpectedly at " + str(rtClock.datetime())
except Exception as error:
    errorHandler("discon message", error, traceback.print_stack())
'''
'''
#set lw&t to notify of disconnect:
disconMsg = "Client " + UID + " has disconnected unexpectedly at " + rtClock.datetime()
client.set_last_will(config["TELEMTOPIC"],disconMsg)

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(ubinascii.hexlify(machine.unique_id()), config["BROKER"], keepalive=60)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(config["CCTOPIC"])
  print('Connected to %s MQTT broker, subscribed to %s topic' % (config["BROKER"], config["CCTOPIC"]))
  return client

client = connect_and_subscribe()
'''
#client = MQTTClient(ubinascii.hexlify(machine.unique_id()), config["BROKER"], keepalive=60)
#move client instantiation up to avoid errors
client.set_callback(sub_cb)
client.set_last_will(statusTopic,json.dumps(disconMsg).encode())

try:
    client.connect()
except Exception as error:
    print(error)
    errorHandler("mqtt connect", error, traceback.print_stack())
else:
    time.sleep(1)
    client.subscribe(ccTopic)
    statusHandler("inital connect", "connected to wifi and mqtt")
    #webrepl.start()
#TODO: mqtt connection checking and error catching, SSL/TLS, mqtt last will

#declare I2C and SPI busses for sensors:
try:
    sensorBus = machine.I2C(0,scl=machine.Pin(12),sda=machine.Pin(11))
    time.sleep(1)
except Exception as error:
    errorHandler("I2C init", error, traceback.print_stack())

#total luminosity sensor:
try:
    totalLuxSense = TSL2591.TSL2591(sensorBus)
    totalLuxSense.gain = TSL2591.GAIN_LOW
    #totalLuxSense.gain = config["SENSORPREF"][1]["GAIN"]
    #totalLuxPresent = True
except Exception as error:
    print(error)
    errorHandler("lux sensor init", error, traceback.print_stack)
    totalLuxPresent = False
else:
    totalLuxPresent = True
#TODO: add totalLuxSense.gain = config["SENSORPREF"]["TSL2591"]["GAIN"]

#spectral triad light sensor:
#add I2C scan to make sure spectral triad is installed
specTriadPresent = True

try:
    specTriad = as7265x.AS7265X(sensorBus)
    time.sleep_ms(500)
    specTriad.disable_indicator()
    time.sleep_ms(500)
    specTriad.disable_bulb(as7265x.AS7265x_LED_WHITE)
    specTriad.disable_bulb(as7265x.AS7265x_LED_IR)
    specTriad.disable_bulb(as7265x.AS7265x_LED_UV)
    time.sleep_ms(500)
except Exception as error:
    print(error)
    specTriadPresent = False
    errorHandler("spec triad init", error, traceback.print_stack())

#TODO: add specTriad.set_gain = config["SENSORPREF"]["TSL2591"]["GAIN"]

#BME 280 Environmental Sensor
try:
    bmeAtmospheric = bme280.BME280(i2c=sensorBus)
except Exception as error:
    errorHandler("BME 280 connection", error, traceback.print_stack())
    print(error)
time.sleep(1)

#SDC40 CO2 Sensor:
try:
    scd40CO2 = scd40.SCD4X(sensorBus)
except Exception as error:
    print("co2 error")
    errorHandler("CO2 instantiate", error, traceback.print_stack())

time.sleep(1)
try:
    scd40CO2.start_periodic_measurement()
except Exception as error:
    errorHandler("CO2 start readings", error, traceback.print_stack())
time.sleep(1)

#TODO: cross checking and correlation between BME 280 and SCD40 for temp, hum

#Onewire Temp Probe Sensors:
tempProbePin = machine.Pin(13)

try:
    tempProbeBus = ds18x20.DS18X20(onewire.OneWire(tempProbePin))
    probeTemps = tempProbeBus.scan()
except Exception as error:
    errorHandler("temp probe init", error, traceback.print_stack())

#Analog Moisture Probe Sensors:
#TODO: THESE PINS ARE ALL WRONG.  PLACEHOLDER
#TODO: publish voltage info regularly, status channel
moistProbePins = [machine.ADC(2,atten=machine.ADC.ATTN_11DB),machine.ADC(3,atten=machine.ADC.ATTN_11DB),machine.ADC(7,atten=machine.ADC.ATTN_11DB)]
#TODO: moisture probe power pin, switch off when not in use.
vBusPin = machine.ADC(4,atten=machine.ADC.ATTN_0DB)
chargeOutPin = machine.ADC(5,atten=machine.ADC.ATTN_0DB)
battPin = machine.ADC(6,atten=machine.ADC.ATTN_0DB)



#Set up the vent fan:
fanEnabled = False
fanOverride = False
fanPin = machine.Pin(1, machine.Pin.OUT)  #THIS IS NOT 4
fanPin.value(0)
fanCyclesOn = 0
fanCyclesOff = 0

def fanControl(ambient, time):
    if not fanEnabled:
        if vBusPin.read_uv() * 11 / 1000000 > 4.0 or battPin.read_uv() * 11 / 1000000 > 4.0:
            if sum(ambient) / 2 >= 25.0:
                if fanCyclesOff > 5 or fanCyclesOff == 0:
                    fanCyclesOff = 0
                    fanEnabled = True
                else:
                    fanCyclesOff += 1
                    fanEnabled = False
            else:
                fanEnabled = False
        else:
            if sum(ambient) / 2 >= 30:
                fanEnabled = True
    else:
        if vBusPin.read_uv() * 11 / 1000000 > 4.0 or battPin.read_uv() * 11 / 1000000 > 4.0:
            if sum(ambient) / 2 > 25:
                fanEnabled = True
            else:
                pass
        else:
            pass
    
    return fanEnabled

#Main logging loop:
def main():
    global fanEnabled
    global fanOverride
    global config
    global offlineMode
    while True:
        tempProbeValues = []
        moistProbeRaw = []
        moistProbeValues = []
        powerData = {"BATT": False,
                     "SOLAR": False,
                     "USB": False,
                     "BATTV": 0.0,
                     "VBUS": 0.0,
                     "VSYS": 0.0,
                     "MAINV": 0.0}
        
        luxData = {"TOTAL":0,
                   "IR":0,
                   "VIS":0,
                   "FULLSPEC":0}
        
        lightSpectrumData = {"IR":
                                 {"R":0.0,
                                  "S":0.0,
                                  "T":0.0,
                                  "U":0.0,
                                  "V":0.0,
                                  "W":0.0
                                  },
                             "VIS":
                                 {"G":0.0,
                                  "H":0.0,
                                  "I":0.0,
                                  "J":0.0,
                                  "K":0.0,
                                  "L":0.0
                                  },
                             "UV":
                                 {"A":0.0,
                                  "B":0.0,
                                  "C":0.0,
                                  "D":0.0,
                                  "E":0.0,
                                  "F":0.0
                                   }
                             }
        atmosphericData = {
                          "BME280":
                               {
                                "TEMP":0.0,
                                "PRESSURE":0.0,
                                "HUMIDITY":0.0,
                                "DEWPOINT":0.0,
                                "ALTITUDE":0.0
                                },
                           "SCD40":
                               {
                                "TEMP":0.0,
                                "HUMIDITY":0.0,
                                "CO2":0.0
                                }
                           }
        
        #Log atmospheric conditions:
        '''
        try:
            scd40CO2.start_periodic_measurement()
        except Exception as error:
            errorHandler("CO2 meas begin", error, traceback.print_stack())
            print(error)
        time.sleep(1)
        '''
        
        try:
            atmosphericData["BME280"]["TEMP"] = bmeAtmospheric.read_compensated_data()[0]
            atmosphericData["BME280"]["PRESSURE"] = bmeAtmospheric.read_compensated_data()[1]
            atmosphericData["BME280"]["HUMIDITY"] = bmeAtmospheric.read_compensated_data()[2]
            atmosphericData["BME280"]["DEWPOINT"] = bmeAtmospheric.dew_point
            #atmosphericData["BME280"]["dewpoint"] = 0
            atmosphericData["BME280"]["ALTITUDE"] = bmeAtmospheric.altitude
            
        except Exception as error:
            print(error)
            errorHandler("BME280 reading", error, traceback.print_stack())
            atmosphericData["BME280"]["TEMP"] = 0
            atmosphericData["BME280"]["PRESSURE"] = 0
            atmosphericData["BME280"]["HUMIDITY"] = 0
            atmosphericData["BME280"]["DEWPOINT"] = 0
            #atmosphericData["BME280"]["dewpoint"] = 0
            atmosphericData["BME280"]["ALTITUDE"] = 0
        
        co2Wait = 0
        while not scd40CO2.data_ready:
            print("waiting on CO2 sensor")
            if co2Wait < 20:
                co2Wait += 1
                time.sleep_ms(500)
            else:
                errorHandler("SCD40 data ready", "timed out waiting for CO2 sensor", "") 
                break
            
        try:
            atmosphericData["SCD40"]["TEMP"] = scd40CO2.temperature
            atmosphericData["SCD40"]["HUMIDITY"] = scd40CO2.relative_humidity
            atmosphericData["SCD40"]["CO2"] = scd40CO2.co2
        except Exception as error:
            errorHandler("SCD40 reading", error, traceback.print_stack())
            atmosphericData["SCD40"]["TEMP"] = 0
            atmosphericData["SCD40"]["HUMIDITY"] = 0
            atmosphericData["SCD40"]["CO2"] = 0
        
        #Log light data:
        if totalLuxPresent == True:
            try:
                luxData["TOTAL"] = totalLuxSense.lux
                luxData["IR"] = totalLuxSense.infrared
                luxData["VIS"] = totalLuxSense.visible
                luxData["FULLSPEC"] = totalLuxSense.full_spectrum
            except Exeption as error:
                errorHandler("lux reading", error, traceback.print_stack())
        else:
            pass
        
        #luxData = [totalLuxSense.lux, totalLuxSense.infrared, totalLuxSense.visible, totalLuxSense.full_spectrum]
        global specTriadPresent
        if specTriadPresent:
            try:
                specTriad.take_measurements()
                
                lightSpectrumData["IR"]["R"] = specTriad.get_calibrated_R()
                lightSpectrumData["IR"]["S"] = specTriad.get_calibrated_S()
                lightSpectrumData["IR"]["T"] = specTriad.get_calibrated_T()
                lightSpectrumData["IR"]["U"] = specTriad.get_calibrated_U()
                lightSpectrumData["IR"]["V"] = specTriad.get_calibrated_V()
                lightSpectrumData["IR"]["W"] = specTriad.get_calibrated_W()
                
                lightSpectrumData["VIS"]["G"] = specTriad.get_calibrated_G()
                lightSpectrumData["VIS"]["H"] = specTriad.get_calibrated_H()
                lightSpectrumData["VIS"]["I"] = specTriad.get_calibrated_I()
                lightSpectrumData["VIS"]["J"] = specTriad.get_calibrated_J()
                lightSpectrumData["VIS"]["K"] = specTriad.get_calibrated_K()
                lightSpectrumData["VIS"]["L"] = specTriad.get_calibrated_L()
                
                lightSpectrumData["UV"]["A"] = specTriad.get_calibrated_A()
                lightSpectrumData["UV"]["B"] = specTriad.get_calibrated_B()
                lightSpectrumData["UV"]["C"] = specTriad.get_calibrated_C()
                lightSpectrumData["UV"]["D"] = specTriad.get_calibrated_D()
                lightSpectrumData["UV"]["E"] = specTriad.get_calibrated_E()
                lightSpectrumData["UV"]["F"] = specTriad.get_calibrated_F()
                
            except Exception as error:
                errorHandler("spectrum reading", error, traceback.print_stack())
            
        else:
            pass

        #Sensor probe readings:
        try:
            tempProbeBus.convert_temp()
            time.sleep_ms(800)
            for i in probeTemps:
                tempProbeValues.append(tempProbeBus.read_temp(i))
                
            for pin in moistProbePins:
                #moistProbeValues.append(pin.read_u16())
                moistProbeRaw.append(pin.read_uv() * 3.3 / 1000000)
                
            for value in moistProbeRaw:
                moistProbeValues.append((value - 1.3)*(100 - 0)/(2.4 - 1.3) + 0)
            
            probeData = {}
            for index, temp in enumerate(tempProbeValues):
                probeData[index] = {"TEMP":temp, "MOIST":moistProbeValues[index]}
                
        except Exception as error:
            print(error)
            errorHandler("probe reading", error, traceback.print_stack())
            probeData = {"TEMP":0.0,"MOIST":0.0}
        #Battery voltage readings:
        #TODO: choose an analog pin and set up appropriate voltage divider, maybe MCP chip
        #TODO: custom exceptions/types
        #TODO: exception logging, data storage in flash while offline, wifi detect/reconnect
       
       
        try:
            powerData["BATTV"] = battPin.read_uv() / 1000000 * 11
            powerData["VBUS"] = vBusPin.read_uv() / 1000000 * 11
            #powerData["US"] = battPin.read_uv() / 1000000 * 11
            
            readings = [0] * 15
            processed = []
            for index, reading in enumerate(readings):
                readings[index] = chargeOutPin.read_uv() / 1000000 * 11
                time.sleep_ms(150)
                
            for reading in readings:
                if reading > statistics.stdev(readings):
                    processed.append(reading)
                    
            powerData["VSYS"] = statistics.mean(processed)
            
            if battPin.read_uv() / 10000000 > 0:
                powerData["BATT"] = True
            else:
                pass
        except Exception as error:
            print(error)
        
       
        #multisampling voltage read:
        
        #build the json payload:
        mqttPayload = {
                        "node": config["NAME"],
                        "UID": UID,
                        "CONTEXT": config["CONTEXT"],
                        "LIGHTSPECTRUM": lightSpectrumData,
                        "LUX": luxData,
                        "ATMOSPHERIC": atmosphericData,
                        "PROBE": probeData,
                        "POWER": powerData,
                        "RTCLOCK": rtClock.datetime(),
                        "MEMFREE": gc.mem_free(),
                        "MEMUSED": gc.mem_alloc(),
                        "FAN": fanEnabled
                       }
        
        mqttPayload = json.dumps(mqttPayload)
        print(mqttPayload)
        if not station.isconnected():
            if offlineMode:
                with open("offlineData.txt",'a') as f:
                    f.write("\n")
                    json.dumps(mqttPayload, f)
                    #add enclosing square brackets to make json array and comma between each json, but not after last
                config["SAVEDDATA"] = True
                with open("config.json",'w') as f:
                    json.dump(config, f)
            else:
                try:
                    station.connect(config["SSID"], config["WIPASS"])
                    wifiAttempts = 0
                    while not station.isconnected():
                        if wifiAttempts < 10:
                            wifiAttempts += 1
                            time.sleep(3)
                            station.connect(config["SSID"], config["WIPASS"])
                        else:
                            if wifiAttempts >= 10 and time.mktime(rtClock.datetime()) - lastConnect > 600:
                                #config["SAVEDDATA"] = True
                                offlineMode = True
                            #TODO: enter longer log interval mode and save data locally
                except Exception as error:
                    errorHandler("wifi recconnect", error, traceback.print_stack())
                finally:
                    if station.isconnected():
                        offlineMode = False
                        try:
                            statusHandler("wifi recconect","wifi connection successfully restablished")
                        except:
                            pass
                    else:
                        pass
        else:
        
            try:
                client.publish(telemTopic, mqttPayload.encode())
                client.check_msg()
            except Exception as error:
                errorHandler("mqtt publish", error, traceback.print_stack())
                try:
                    client.connect()
                    client.publish(telemTopic, mqttPayload.encode())
                    client.subscribe(ccTopic)
                    '''
                    if config["SAVEDDATA"]:
                        pass
                        #for line in file, publish each, change flag, delete saved
                    '''
                    #client.check_msg()
                except Exception as error:
                    errorHandler("mqtt reconnect", error, traceback.print_stack())
                    #pass
                else:
                    offlineMode = False
                try:
                    client.check_msg()
                except Exception as error:
                    errorHandler("mqtt message check", error, traceback.print_stack())
        #TODO: if time.mktime(rtClock.datetime) - lastUpdateCheck > 1 day, run updater
        #time.sleep(10)
                    
        if station.isconnected() and config["SAVEDDATA"]:
            try:
                if "offlineData.txt" in os.listdir():
                    with open("offlineData.txt",'r') as f:
                        for payload in f.readlines():
                            if payload == "\n":
                                pass
                            else:
                                client.publish(telemTopic,json.dumps(payload).encode())
                                time.sleep(2)
                else:
                    config["SAVEDDATA"] = False
                    with open("config.json",'w') as f:
                        json.dump(config,f)
                
            except Exception as error:
                errorHandler("offline data publish", error, traceback.print_stack())
                #iterate through jsons in file and publish
            else:
                config["SAVEDDATA"] = False
                with open("config.json",'w') as f:
                    json.dump(config,f)
                try:
                    os.remove("offlineData.txt")
                except:
                    pass
                           
        if offlineMode:
            time.sleep(config["OFFLINELOGINTERVAL"])
        else:
            time.sleep(config["LOGINTERVAL"])
        
        #TODO: power detection for fan control
        #fanPin.value(fanCheck)
        '''    
        if atmosphericData["SCD40"]["TEMP"] >= 22:
            fanEnabled = True
            fanPin.value(1)
        else:
            fanPin.value(0)
        '''    
        if fanOverride == True:
            pass
        else:
            if atmosphericData["SCD40"]["TEMP"] >= 25:
                fanEnabled = True
                fanPin.value(1)
            else:
                fanEnabled = False
                fanPin.value(0)
                
        print(gc.mem_free())
        gc.collect()
        print(gc.mem_free())
        if gc.mem_free() * 1.5 < gc.mem_alloc():
            print("low mem")
            #memDog.feed()
        else:
            pass
        
        try:
            statusHandler("logging loop", "all systems normal")
        except:
            pass
                        
main()                        

