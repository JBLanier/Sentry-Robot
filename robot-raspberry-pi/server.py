from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor
from aiohttp import web
import atexit
import math
import asyncio
import time
import socketio
import Adafruit_LSM303
import threading


# create a default object, no changes to I2C address or frequency
mh = Adafruit_MotorHAT(addr=0x60)
lsm303 = Adafruit_LSM303.LSM303()

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

atexit.register(turnOffMotors)

loadMotor = mh.getMotor(1)
xMotor = mh.getMotor(2)
yMotor = mh.getMotor(3)
fireMotor = mh.getMotor(4)

loadMotor.setSpeed(160)
fireMotor.setSpeed(255)

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

isFiring = False
restrictDownMovement = False
restrictUpMovement = False
searching = False


def checkTilt():
   global restrictDownMovement, restrictUpMovement, centerMag, centerAccel 
   while(1):
        accel, mag = lsm303.read()
        accel_x, accel_y, accel_z = accel
        mag_x, mag_z, mag_y = mag
        
        #print('Accel x: ' + str(accel_x) + ' y: ' + str(accel_y) + ' z: ' +str(accel_z) + ' | Mag x: ' + str(mag_x) + ' y: ' + str(mag_y) + ' z: ' + str(mag_z), end='\r')
        
        if (accel_x) < -380:
            yMotor.run(Adafruit_MotorHAT.RELEASE)
            print("restrict UP")
            restrictUpMovement = True
        else:
            restrictUpMovement = False
        if (accel_x) > 140:
            yMotor.run(Adafruit_MotorHAT.RELEASE)
            print("restrict Down")
            restrictDownMovement = True
        else:
            restrictDownMovement = False
        time.sleep(0.1)

async def index(request):
    """Serve the client-side application."""
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')

@sio.on('connect', namespace='/robot')
def connect(sid, environ):
    print("connect ", sid)


@sio.on('search', namespace='/robot')
def search(sid,data):
    t = threading.Thread(target=execute_search)
    t.start()

def execute_search():
    global searching
    print ('searching')
    searching = True
    i = 0
    j = 0
    increment = True
    while searching:
        print(searching)
        if increment:
            xMotor.setSpeed(150)
            xMotor.run(Adafruit_MotorHAT.BACKWARD)
            i = i + 1
        else:
            xMotor.setSpeed(150)
            xMotor.run(Adafruit_MotorHAT.FORWARD)
            i = i - 1
        time.sleep(0.4)

        xMotor.run(Adafruit_MotorHAT.RELEASE)
        yMotor.run(Adafruit_MotorHAT.RELEASE)
        time.sleep(0.2)

        if i == 3:
            increment = False
        if i == -3:
            increment = True
        if i == 0:
            j = j + 1
            if (j == 3):
                searching = False
                break 
    xMotor.run(Adafruit_MotorHAT.RELEASE)
    yMotor.run(Adafruit_MotorHAT.RELEASE)
    
@sio.on('move', namespace='/robot')
def move(sid, data):
    global searching
    searching = False
    #print("control")

    x = data["right"] * 220
    y = data["up"] * 170
    
    if abs(x) > 120:    
        if x < 0:
            xMotor.setSpeed(int(math.floor(x * -1)))
            xMotor.run(Adafruit_MotorHAT.BACKWARD)
        else:
            xMotor.setSpeed(int(math.floor(x)))
            xMotor.run(Adafruit_MotorHAT.FORWARD)
    else:
        xMotor.run(Adafruit_MotorHAT.RELEASE)   

    if abs(y) > 80:
        if y < 0:
            if not restrictDownMovement:
                yMotor.setSpeed(int(math.floor(y * -1)))
                yMotor.run(Adafruit_MotorHAT.BACKWARD)
            else:
                yMotor.run(Adafruit_MotorHAT.RELEASE)
        else:
            if not restrictUpMovement:
                yMotor.setSpeed(int(math.floor(y)))
                yMotor.run(Adafruit_MotorHAT.FORWARD)
            else:
                yMotor.run(Adafruit_MotorHAT.RELEASE)
    else:
        yMotor.run(Adafruit_MotorHAT.RELEASE)
    

@sio.on('kill', namespace='/robot')
def kill(sid, data):
    global searching
    searching = False
    xMotor.run(Adafruit_MotorHAT.RELEASE)
    yMotor.run(Adafruit_MotorHAT.RELEASE)
    #print("kill ", data)
        

@sio.on('fire', namespace='/robot')
def fire(sid, data):
    global isFiring, searching
    searching = False
    print("fire ", data)
    if not isFiring:    
        isFiring = True
        turnOffMotors()       
        fireMotor.run(Adafruit_MotorHAT.FORWARD)
        time.sleep(1.7)
        loadMotor.run(Adafruit_MotorHAT.BACKWARD)
        time.sleep(1.2)
        loadMotor.run(Adafruit_MotorHAT.RELEASE)
        time.sleep(1)
        turnOffMotors()
        isFiring = False

@sio.on('disconnect', namespace='/robot')
def disconnect(sid):
    print('disconnect ', sid)


app.router.add_static('/static', 'static')
app.router.add_get('/', index)


if __name__ == '__main__':
    t = threading.Thread(target=checkTilt)
    t.start()
    web.run_app(app, port=80)    
    t.join(1)
