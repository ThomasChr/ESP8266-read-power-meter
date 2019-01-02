import time
import machine
import network
import usocket

# Globals
debug = 0
sensorid = 5
sendseconds = 60
secondstrywificonnect = 20
totblinks = 0
# GPIO 5 is Pin D1 on NodeMCU
pinwithIRsensor = 5
wifiname = '1'
wifipass = '2'
serveraddress = 'myserver.de'
passforsending = '3'
messA = 0
messB = 0

if debug:
    print(str(time.ticks_ms()) + ': ***STARTUP***')
    print(str(time.ticks_ms()) + ': sensorid: ' + str(sensorid))
    print(str(time.ticks_ms()) + ': sendseconds: ' + str(sendseconds))
    print(str(time.ticks_ms()) + ': secondstrywificonnect: ' + str(secondstrywificonnect))
    print(str(time.ticks_ms()) + ': pinwithIRsensor: ' + str(pinwithIRsensor))
    print(str(time.ticks_ms()) + ': wifiname: ' + str(wifiname))
    print(str(time.ticks_ms()) + ': wifipass: ' + str(wifipass))
    print(str(time.ticks_ms()) + ': serveraddress: ' + str(serveraddress))
    print(str(time.ticks_ms()) + ': passforsending: ' + str(passforsending))

# This function will send our Data to the Internet
def senddata(timer):
    # Any exception will return
    try:
        global messA
        global messB
        global totblinks
        if debug:
            print(str(time.ticks_ms()) + ': ***senddata***')
            print(str(time.ticks_ms()) + ': messA ' + str(messA))
            print(str(time.ticks_ms()) + ': messB ' + str(messB))
            print(str(time.ticks_ms()) + ': totblinks ' + str(totblinks))
        if messA == 0 or messB == 0:
            if debug:
                print(str(time.ticks_ms()) + ': messA or messB == 0 -> returning')
            return
        if abs(messA - messB) > 3600000:
            if debug:
                print(str(time.ticks_ms()) + ': Possible Overflow')
            if messA > messB:
                if debug:
                    print(str(time.ticks_ms()) + ': Setting messA to 0')
                messA = 0
            if messB > messA:
                if debug:
                    print(str(time.ticks_ms()) + ': Setting messA to 0')
                messB = 0
            return
        if messA > messB:
            timebetweenpulses = messA - messB
        else:
            timebetweenpulses = messB - messA
        watt = 360000 / timebetweenpulses
        if totblinks > 0:
            kwh_since_start = totblinks / 10000
        else:
            kwh_since_start = 0
        if debug:
            print(str(time.ticks_ms()) + ': timebetweenpulses (ms) ' + str(timebetweenpulses))
            print(str(time.ticks_ms()) + ': watt ' + str(watt))
            print(str(time.ticks_ms()) + ': kwh_since_start ' + str(kwh_since_start))
        # Connect to WiFi -> Get interfaces
        sta_if = network.WLAN(network.STA_IF)
        ap_if = network.WLAN(network.AP_IF)
        # Deactivate access point, we're station only
        ap_if.active(False)
        # Now connect
        connectcount = 0
        if not sta_if.isconnected():
            sta_if.active(True)
            sta_if.connect(wifiname, wifipass)
            while not sta_if.isconnected():
                connectcount = connectcount + 1
                time.sleep(1)
                if debug:
                    print(str(time.ticks_ms()) + ': Connect try: ' + str(connectcount))
                if connectcount > secondstrywificonnect:
                    # We didn't connect after secondstrywificonnect seconds. Let's sleep
                    if debug:
                        print(str(time.ticks_ms()) + ': Connect failed after ' + str(connectcount) + ' seconds sleep. Giving up.')
                    return
        # Send data to the Internet, a Post Request with http - we don't use SSL here!
        content = b'sensorid=' + str(sensorid) + '&power=' + str(watt) + '&kwh_since_start=' + str(kwh_since_start) + '&password=' + passforsending
        if debug:
            print(str(time.ticks_ms()) + ': Connecting to website')
        addr_info = usocket.getaddrinfo(serveraddress, 80)
        addr = addr_info[0][-1]
        sock = usocket.socket()
        sock.connect(addr)
        sock.send(b'POST /tempsensor.php HTTP/1.1\r\n')
        sock.send(b'Host: ' + serveraddress + b'\r\n')
        sock.send(b'Content-Type: application/x-www-form-urlencoded\r\n')
        sock.send(b'Content-Length: ' + str(len(content)) + '\r\n')
        sock.send(b'\r\n')
        if debug:
            print(str(time.ticks_ms()) + ': Sending: ' + str(content))
        sock.send(content)
        sock.send(b'\r\n\r\n')
        if debug:
            print(str(time.ticks_ms()) + ': Answer: ' + str(sock.recv(1000)))
        sock.close()
        messA = 0
        messB = 0
    except:
        if debug:
            print(str(time.ticks_ms()) + ': Exception in senddata() happend. Returning')
        return

# This function is called everytime we get a pulse
def blinkarrived(pin):
    # Any exception will return
    try:
        global messA
        global messB
        global totblinks
        if debug:
            print(str(time.ticks_ms()) + ': ***blinkarrived***')
            print(str(time.ticks_ms()) + ': messA ' + str(messA))
            print(str(time.ticks_ms()) + ': messB ' + str(messB))
            print(str(time.ticks_ms()) + ': totblinks ' + str(totblinks))
        akttime = time.ticks_ms()
        totblinks = totblinks + 1
        if messA > messB:
            messB = akttime
            if debug:
                print(str(time.ticks_ms()) + ': Setting messB to: ' + str(akttime))
            return
        else:
            messA = akttime
            if debug:
                print(str(time.ticks_ms()) + ': Setting messA to: ' + str(akttime))
            return
    except:
        if debug:
            print(str(time.ticks_ms()) + ': Exception in blinkarrived() happend. Returning')
        return

# Any exception will reset us
try:
    # Activate a timer which will send our last sample every sendseconds Seconds
    if debug:
        print(str(time.ticks_ms()) + ': Activating Timer')
    tim = machine.Timer(-1)
    tim.init(period = sendseconds * 1000, mode = machine.Timer.PERIODIC, callback = senddata)
    # Activate a callback everytime we get a blink
    if debug:
        print(str(time.ticks_ms()) + ': Activating Interrupt')
    irsensor = machine.Pin(pinwithIRsensor, machine.Pin.IN, machine.Pin.PULL_UP)
    irsensor.irq(trigger = machine.Pin.IRQ_RISING, handler = blinkarrived)
except:
    if debug:
        print(str(time.ticks_ms()) + ': Exception in main() happend. RESTART')
    machine.reset()
