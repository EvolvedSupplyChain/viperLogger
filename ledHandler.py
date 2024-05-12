'''
ledHandler.py
Status LED handler
ESC Viper Logging Suite
REQUIRED
A. Liebig for ESC
5/2/24
Version 1.7
'''
import machine
import neopixel
import _thread
import random
import time

#constants:
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
off = (0,0,0)
white = (255,255,255)


class ledController:
    def __init__(self, pin, length):
        self.pin = machine.Pin(pin,machine.Pin.OUT)
        self.length = length
        self.np = neopixel.NeoPixel(pin,length)
        self.all_off_now()
        
    def blink(self, color, cycles, **kwargs):
        runForever = False
        if cycles < 1:
            runForever = True
            cycles = 10
        else:
            pass
        if "interval" in kwargs.keys():
            for key in kwargs:
                if key == 'num':
                    for j in range(cycles):
                        self.np[kwargs['num']] = color
                        self.np.write()
                        time.sleep(kwargs['interval'])
                        self.np[kwargs['num']] = off
                        self.np.write()
                        time.sleep(kwargs['interval'])
                        if runForever:
                            pass
                        else:
                            j+=1
                    
                elif key == 'start' or key == 'end':
                    for j in range(cycles):
                        for i in range(kwargs['start'],kwargs['end']):
                            self.np[i] = color
                        self.np.write()
                        time.sleep(kwargs['interval'])
                        for i in range(kwargs['start'],kwargs['end']):
                            self.np[i] = off
                        self.np.write()
                        time.sleep(kwargs['interval'])
                        if runForever:
                            pass
                        else:
                            j+=1
                        
        elif "timeOn" in kwargs.keys() and "timeOff" in kwargs.keys():
            for key in kwargs:
                if key == 'num':
                    for j in range(cycles):
                        self.np[kwargs['num']] = color
                        self.np.write()
                        time.sleep(kwargs['timeOn'])
                        self.np[kwargs['num']] = off
                        self.np.write()
                        time.sleep(kwargs['timeOff'])
                        if runForever:
                            pass
                        else:
                            j+=1
                    
                elif key == 'start' or key == 'end':
                    for j in range(cycles):
                        for i in range(kwargs['start'],kwargs['end']):
                            self.np[i] = color
                        self.np.write()
                        time.sleep(kwargs['timeOn'])
                        for i in range(kwargs['start'],kwargs['end']):
                            self.np[i] = off
                        self.np.write()
                        time.sleep(kwargs['timeOff'])
                        if runForever:
                            pass
                        else:
                            j+=1
        else:
            pass
    
    def blink_threaded(self, color, cycles, **kwargs):
        #args = kwargs
        kws = kwargs
        #_thread.start_new_thread(self.blink,(self, color, cycles),kwargs))
        _thread.start_new_thread(self.blink,(self,color,cycles),**kws)
    
    
    def set_single(self,color,num):
        self.np[num] = color
        
    def set_range(self,color,start,end):
        for i in range(start,end):
            self.np[i] = color
        
    def all_off(self):
        for i in range(self.length):
            self.np[i] = off
            
    def all_off_now(self):
        for i in range(self.length):
            self.np[i] = off
            self.np.write()
            
    def all_on(self, color):
        for i in range(self.length):
            self.np[i] = color
            
    def all_on_now(self, color):
        for i in range(self.length):
            self.np[i] = color
            self.np.write()
        
    def light_show(self):
        while True:
            for i in range(self.length):
                self.np[i] = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
            self.np.write()
            time.sleep(random.random())
            
    def update_strip(self):
        self.np.write()
            
            