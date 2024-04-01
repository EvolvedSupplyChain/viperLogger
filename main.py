import os
import time
import gc
from ota import OTAUpdater
from machine import reset
from machine import Pin

gc.collect()

try:
    z = open("updateLog.txt",'a')
except Exception as error:
    print(error)
    z = open("updateLog.txt",'w')
    z.write(error)

#check if there is an update install pending and how many boot cycles have passed:
try:
    g = open("updateFlag.txt","r+")
    doUpdate = int(g.read())
    #g.close()
except Exception as error:
    print(error)
    doUpdate = 0
    g = open("updateFlag.txt",'w')
    g.write(str(doUpdate))
    g.close()
    
try:
    f = open('bootCount.txt','r')
    #time.sleep(1)
    count = int(f.read())
    #time.sleep(1)
    #print(count)
    f.close()
except Exception as error:
    print(error)
    count = 0
    f = open('bootCount.txt','w')
    f.write(str(count))
    f.close()
    

#f.close()
#time.sleep(1)
#f = open('bootCount.txt','w')
#time.sleep(1)

#print(count)

#f = open('bootCount.txt','w')

k = open("updateConfig.txt",'r')
#updateSettings = k.read()
updateSettings = json.load(k)
k.close()
'''
if doUpdate == 1:
    firmware_url = "https://raw.githubusercontent.com/EvolvedSupplyChain/agriculture/main/"
    otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, "logger.py")
    count = 0
    f.write(str(count))
    f.close()
    g.write(str(0))
    g.close()
    otaClient.download_and_install_update_if_available()
'''
if doUpdate == 1:
    firmware_url = updateSettings["Repo"] + '/' + updateSettings["Branch"]
    filename = updateSettings["Files"]
    otaClient = OTAUpdater(secretVars.ssid, secretVars.wifiPassword, firmware_url, filename)
else:
    if count < 2:
        count = count + 1
        t = open("bootCount.txt",'w')
        t.write(str(count))
        t.close()
        sleep(1)
        reset()
    else:
        gc.collect()
        import logger
        logger.main()
    
'''    
else:
    if 'latest_code.py' in os.listdir():
        #f = open("bootCount.txt",'w')
        #f.write(
        os.remove('logger.py')
        time.sleep(3)
        os.rename('latest_code.py', 'logger.py')
        time.sleep(3)
        #os.remove('latest_code.py')
        #time.sleep(3)
        #f = open('bootCount.txt','w')
        time.sleep(3)
        f.write("0")
        time.sleep(3)
        f.close()
        time.sleep(5)
        machine.reset()
    else:
        if count < 2:
            print(count)
            count = count + 1
            print(count)
            #f = open('bootCount.txt','w')
            time.sleep(3)
            f.write(str(count))
            time.sleep(5)
            f.close()
            time.sleep(5)
            #print(count)
            machine.reset()
            
        else:
            f.write("0")
            time.sleep(3)
            f.close()
            #os.remove('bootCount.txt')
            time.sleep(5)    
            import logger
            time.sleep(5)
            #logger.main()
'''