import utime
#import os
import time
import bmp280
import aht10
import onewire
import ds18x20
import as7265x
import TSL2591
import network
import socket
import secretVars
import ubinascii
import json
import gc
import struct
from camera import *
from umqttsimple import MQTTClient
#from ota import OTAUpdater
from machine import Pin, SPI, I2C, ADC, RTC, unique_id

gc.collect()

logTime = 5


print("OTA debug day two take 3")
#from Arducam import *
#from camera import *

'''OTA Updater'''
#firmware_url = "https://raw.githubusercontent.com/EvolvedSupplyChain/agriculture/main/"
#updateFile = "main.py"
#updateFilesList = []

#otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, "logger.py")
#otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, updateFile)
#otaClient.download_and_install_update_if_available()
#otaClient.download_and_install_update_if_available()

time.sleep(3)

'''wifi connection:'''
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(secretVars.ssid, secretVars.wifiPassword)

time.sleep(3)

while station.isconnected() == False:
    pass
print(station.ifconfig())

time.sleep(2)
'''Time Check and Clock Set:'''
NTP_DELTA = 2208988800   #Adjust this for time zone
timeHost = "pool.ntp.org"
rtClock = RTC()

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
    finally:
        s.close()

    #Set our internal time
    val = struct.unpack("!I", msg[40:44])[0]
    tm = val - NTP_DELTA    
    t = time.gmtime(tm)
    rtClock.datetime((t[0],t[1],t[2],t[6]+1,t[3],t[4],t[5],0))

set_time()
time.sleep(2)
print(time.localtime())
lastUpdateCheck = time.time()

'''OTA Updater'''
#firmware_url = "https://raw.githubusercontent.com/EvolvedSupplyChain/agriculture/main/"
#updateFile = "main.py"
#updateFilesList = []

#otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, "main.py")
#otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, updateFile)
#otaClient.download_and_install_update_if_available()'''


'''MQTT:'''

def sub_cb(topic, msg):
  print((topic, msg))
  if topic == secretVars.ccTopic:
    decodedMsg = json.loads(msg)
    subject = decodedMsg.get("subject")
    #print('Topic: ' + topic + 'Message: ' + msg)
    if subject == b"returnSettings":
        theSettings = {
            "loggingInterval": logTime,
            "spectralGain": "16x"
            }
        client.publish(secretVars.ccTopic, json.dumps(theSettings).encode())
    elif subject == b"changeSettings":
        #change device settings
        pass
    elif subject == b"checkForUpdate":
        #otaClient.download_and_install_update_if_available()
        #client.publish(secretVars.ccTopic, b"Checking for updates...")
        v = open("updateFlag.txt","w")
        v.write("1")
        v.close()
        machine.reset()
    '''match msg:
        case "setProp":
            print(msg)
        case "reboot":
            print(msg)
        case _:
            print(msg)'''
            #parse the incoming JSON and extract some "messageType" variable, take appropriate action 
        
  else:
    print('message recieved: ' + msg)

def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  client = MQTTClient(secretVars.clientID, secretVars.brokerAddress, keepalive=60)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(secretVars.ccTopic)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (secretVars.brokerAddress, secretVars.ccTopic))
  return client

client = connect_and_subscribe()


#pre allocate the image variables to avoid fragmentation issues:
gc.collect()
#theBytes = bytearray(16000)
#the64Bytes = bytearray(6000)
#otaClient.download_and_install_update_if_available()

'''ambient temp, humidity, and pressure sensors:'''
ambientPower = Pin(22, Pin.OUT)
ambientPower.value(1)
time.sleep(1)
ambientI2CBus = I2C(0,scl=Pin(1),sda=Pin(0))
time.sleep(2)
tempHum = aht10.AHT10(ambientI2CBus)
time.sleep(2)
tempPres = bmp280.BMP280(ambientI2CBus)
time.sleep(2)
tempPres.use_case(bmp280.BMP280_CASE_INDOOR)
time.sleep(2)

'''spectral and lux sensors:'''
lightPower = Pin(20, Pin.OUT)
lightPower.value(1)
time.sleep(3)
spectralI2CBus = I2C(1,scl=Pin(7),sda=Pin(6))
time.sleep(3)
specTriad = as7265x.AS7265X(spectralI2CBus)
time.sleep(3)
specTriad.disable_indicator()
time.sleep_ms(500)
specTriad.disable_bulb(as7265x.AS7265x_LED_WHITE)
specTriad.disable_bulb(as7265x.AS7265x_LED_IR)
specTriad.disable_bulb(as7265x.AS7265x_LED_UV)
time.sleep_ms(500)
#specTriad.set_measurement_mode(as7265x.AS7265X_MEASUREMENT_MODE_6CHAN_CONTINUOUS)
#specTriad.begin()
#specTriad.disableBulb(as7265x.LED_WHITE)
#specTriad.disableBulb(as7265x.LED_IR)
#specTriad.disableBulb(as7265x.LED_UV)
#luxSense = tsl2591.Tsl2591(spectralI2CBus)
luxSense = TSL2591.TSL2591(spectralI2CBus)

'''temp and moisture probes:'''
tempProbeData = Pin(2)
tempProbePower = Pin(3, Pin.OUT)
tempProbePower.value(1)
#moistureProbeData = Pin(4, Pin.IN)
moistureProbeDataPin = Pin(26, Pin.IN)
moistureProbeData = ADC(moistureProbeDataPin)
offsetPin = ADC(Pin(27, Pin.IN))

#moistureProbeData = ADC(0)

moistureProbePower = Pin(21,Pin.OUT)
moistureProbePower.value(1)

'''Camera:'''

#take_image()
#time.sleep(3)


'''analog data mapping function:'''
def convert(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

'''update call'''
#run the RTC NTP update
#open a text file with logs of previous updates and update checks
#compare last update check time from file to clock
#run updater if needed, log details and close the file
#collect garbage

#listen on MQTT command channel for forced update

'''main program:'''
def main():
    #testMsg = bytearray(15000)
    #run the updater
    #otaClient.download_and_install_update_if_available()
    #check for MQTT messages
    
    
    #check the clock and compare to update flag, run update function if needed
    
    tempBus = ds18x20.DS18X20(onewire.OneWire(tempProbeData))
    temps = tempBus.scan()
    
    while True:
        
        soilMoist = 0
        tempList = []
        tempBus.convert_temp()
        time.sleep_ms(800)
        for i in temps:
            tempList.append(tempBus.read_temp(i))
        
        #ambientData = [0,tempPres.temperature,tempPres.pressure,0]
        
        #ambientData = [tempHum.temperature(),tempPres.temperature,tempPres.pressure,tempHum.humidity()]
        ambientData = [tempHum.temperature(),tempPres.temperature,tempPres.pressure,tempHum.humidity(),tempHum.dew_point()]
        
        
        #moistureProbePower.value(1)
        time.sleep(2)
        soilMoist = moistureProbeData.read_u16()
        offsetReading = offsetPin.read_u16()
        time.sleep_ms(500)
        print(soilMoist)
        print(offsetReading)
        
        soilMoist = soilMoist - offsetReading
        
        soilMoist = soilMoist * 3.2 / 65535
        #moistureProbePower.value(0)
        #soilMoist = soilMoist * (3.3 / 65535) 
        #soilMoist = (3.3 - soilMoist) / 3.3 * 100
        #soilMoist = convert(soilMoist, 0, 65535, 100, 0)
        
        
        
        #fullLux, irLux = luxSense.get_full_luminosity()
        #totalLux = luxSense.calculate_lux(fullLux, irLux)
        fullLux = [luxSense.lux, luxSense.infrared, luxSense.visible, luxSense.full_spectrum]
        
        
        specTriad.take_measurements()
        specData = []
        specData.append(specTriad.get_calibrated_A())
        specData.append(specTriad.get_calibrated_B())
        specData.append(specTriad.get_calibrated_C())
        specData.append(specTriad.get_calibrated_D())
        specData.append(specTriad.get_calibrated_E())
        specData.append(specTriad.get_calibrated_F())
        specData.append(specTriad.get_calibrated_G())
        specData.append(specTriad.get_calibrated_H())
        specData.append(specTriad.get_calibrated_R())        
        specData.append(specTriad.get_calibrated_I())
        specData.append(specTriad.get_calibrated_S())
        specData.append(specTriad.get_calibrated_J())
        specData.append(specTriad.get_calibrated_T())
        specData.append(specTriad.get_calibrated_U())
        specData.append(specTriad.get_calibrated_V())
        specData.append(specTriad.get_calibrated_W())
        specData.append(specTriad.get_calibrated_K())
        specData.append(specTriad.get_calibrated_L())
        
        
        '''debug
        print("Probe Temp:")
        print(tempList)
        print("Ambient data (Temp, Temp, Pressure, Humidity):")
        print(ambientData)
        print("Soil moisture:")
        print(soilMoist)
        print("Luminosity:")
        print(fullLux)
        #print(fullLux, irLux, totalLux)
        print("Spectral Data (ABCDEFGHRISJTUVWKL):")
        print(specData) 
        
        #take_image()
        time.sleep(1)

        '''
        #ahtTest = str(tempHum.print())
        #ahtTemp = tempHum.temperature()
        #ahtHum = tempHum.humidity()
        #tempList = []
        #tempBus.convert_temp()
        #time.sleep_ms(800)
        
        #for i in temps:
        #    tempList.append(tempBus.read_temp(i))
        '''
        #print(tempList)
        #moist = analogMoist.read_u16() * 3.3 / 65536
        #print(moist)
        #print(ahtTest)
        
        
        
        #tempFile = open("image.jpeg",'r')
        #imageData = tempFile.read()
        #tempFile.close()
        '''
        '''
        global theBytes
        global the64Bytes
        print(gc.mem_free())
        gc.collect()
        time.sleep(1)
        
        q = open("image.jpeg","rb")
        theBytes = q.read()
        q.close()
        time.sleep(2)
        #t = open("image.txt","wb")
        #t.write(theBytes)
        #t.close()
        time.sleep(2)
        #os.remove("image.jpeg")
        time.sleep(2)
        #del theBytes
        gc.collect()
        #print(gc.mem_free())
        #gc.collect()
        time.sleep(1)
        print(gc.mem_free())
        the64Bytes = ubinascii.b2a_base64(t.read())
        time.sleep(1)
        #t.close()
        #del theBytes
        gc.collect()
        print(gc.mem_free())
        the64String = the64Bytes.decode('utf-8')
        
        time.sleep(1)
        del the64Bytes
        gc.collect()
        print(gc.mem_free())'''
        
        gc.collect()
        print("message construct mem:")
        print(gc.mem_free())
        '''
        testMsg = {"node": secretVars.nodeID,
                   "unitName": secretVars.unitName,
                   "UID": unique_id(),
                   "soilTemp": tempList,
                   "soilMoist": soilMoist,
                   "ambTemp1": ambientData[0],
                   "ambTemp2": ambientData[1],
                   "ambPres": ambientData[2],
                   "ambHum": ambientData[3],
                   "dewPoint": ambientData[4], 
                   "lux": fullLux,
                   "spectral": specData,
                   "imageData": the64String,
                   "softwareVersion": 8.1
                   }
        '''
        
        testMsg = {"node": secretVars.nodeID,
                   "unitName": secretVars.unitName,
                   "UID": unique_id(),
                   "soilTemp": tempList,
                   "soilMoist": soilMoist,
                   "ambTemp1": ambientData[0],
                   "ambTemp2": ambientData[1],
                   "ambPres": ambientData[2],
                   "ambHum": ambientData[3],
                   "dewPoint": ambientData[4], 
                   "lux": fullLux,
                   "spectral": specData,
                   "softwareVersion": 8.1
                   }
        #print(json.dumps(testMsg).encode())
        client.publish(secretVars.telemTopic, json.dumps(testMsg).encode())
        
        del testMsg
        del tempList
        del soilMoist
        del ambientData
        del fullLux
        del specData
        gc.collect()
        '''
        take_image()
        time.sleep(3)
        #global theBytes
        #global the64Bytes
        print("first mem:")
        print(gc.mem_free())
        gc.collect()
        time.sleep(1)
        
        q = open("image.jpeg","rb")
        theBytes = q.read()
        q.close()
        time.sleep(2)
        print("second mem:")
        print(gc.mem_free())
        
        #t = open("image.txt","wb")
        #t.write(theBytes)
        #t.close()
        #time.sleep(2)
        #os.remove("image.jpeg")
        time.sleep(2)
        #del theBytes
        gc.collect()
        print("third mem")
        print(gc.mem_free())
        #gc.collect()
        time.sleep(1)
        print(gc.mem_free())
        the64Bytes = ubinascii.b2a_base64(theBytes)
        time.sleep(1)
        #t.close()
        del theBytes
        gc.collect()
        print("clear bytes:")
        print(gc.mem_free())
        the64String = the64Bytes.decode('utf-8')
        
        time.sleep(1)
        del the64Bytes
        gc.collect()
        print("clear 64 bytes:")
        print(gc.mem_free())
        
        testMsg2 = {"node": secretVars.nodeID,
                    "unitName": secretVars.unitName,
                    "imageData": the64String
                    }
        
        client.publish(secretVars.telemTopic, json.dumps(testMsg2).encode())
        '''
        #collect garbage and close files
        
        time.sleep(logTime)
        
        client.check_msg()
        global lastUpdateCheck
        timeDiff = time.time() - lastUpdateCheck
        
        if timeDiff > 86400:
            #global lastUpdateCheck
            #lastUpdateCheck = time.time()
            #otaClient.download_and_install_update_if_available()
            print(time.time() - lastUpdateCheck)
            time.sleep(2)
            lastUpdateCheck = time.time()
            time.sleep(2)
            #otaClient.download_and_install_update_if_available()
            s = open("updateFlag.txt","w")
            s.write("1")
            s.close()
            machine.reset()
        else:
            pass

main()
 

