import time as utime
from Arducam import *
#import ubinascii

mode = 0
start_capture = 0
stop_flag=0
#once_number=16
once_number=128
value_command=0
flag_command=0
buffer=bytearray(once_number)

mycam = ArducamClass(OV5642)
mycam.Camera_Detection()
mycam.Spi_Test()
mycam.Camera_Init()
mycam.Spi_write(ARDUCHIP_TIM,VSYNC_LEVEL_MASK)
utime.sleep(1)
mycam.clear_fifo_flag()
#mycam.Spi_write(ARDUCHIP_FRAMES,0x00)
#mycam.OV5642_set_JPEG_size(ov5642_640x480)
mycam.OV5642_set_JPEG_size(ov5642_320x240)

# Arducam functions
def read_fifo_burst():
    count=0
    lenght=mycam.read_fifo_length()
    mycam.SPI_CS_LOW()
    mycam.set_fifo_burst()
    open("image.jpeg", "wb").close()
    f = open("image.jpeg", "ab")
    
    while True:
        #mycam.spi.readinto(buffer,start=0,end=once_number)
        mycam.spi.readinto(buffer)

        f.write(buffer)
        f.flush()

        utime.sleep(0.00015)
        count+=once_number
        if count+once_number>lenght:
            count=lenght-count
            #mycam.spi.readinto(buffer,start=0,end=count)
            mycam.spi.readinto(buffer)

            f.write(buffer)
            f.flush()
            print(f"Image Complete")
            
            mycam.SPI_CS_HIGH()
            mycam.clear_fifo_flag()
            break
    #converted = ubinascii.b2a_base64(f.read())
    f.close()
    #print(converted)
    #k = open('image.txt','w')
    #k.write(converted)
    #k.close()

def take_image():
    while True:
        mycam.flush_fifo()
        mycam.clear_fifo_flag()
        mycam.start_capture()
        utime.sleep(1)
        print(f"Taking Image")
        if mycam.get_bit(ARDUCHIP_TRIG,CAP_DONE_MASK)!=0:
            read_fifo_burst()
            break