import os
import sys
import time
import machine
import network
import usocket
import ubinascii

# Should we output debug messages over serial?
debug = 0
# Should we write a file called except.log everytime there is an exception?
exceptionlog = 1
# Should we send the file to our server as BASE64 exceptiondata?
sendexception = 1
# What is our sensorid?
sensorid = 5
# How many seconds between sending data?
sendseconds = 60
# How many seconds do we try until we abort connecting to our Wifi?
secondstrywificonnect = 30
# How many blinks does or power meter give per kWh
impulses_per_kwh = 10000
# GPIO 5 is Pin D1 on NodeMCU
pinwithIRsensor = 5
# Wifidata
wifiname = '1'
wifipass = '2'
# Serverdata
serveraddress = 'myserver.de'
passforsending = '3'
# Blinks we've seen from our power meter since startup
totblinks = 0
# These are
messA = 0
messB = 0

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
        watt = (36 * impulses_per_kwh) / timebetweenpulses
        if totblinks > 0:
            kwh_since_start = totblinks / impulses_per_kwh
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
        if sendexception and 'except.log' in os.listdir():
            f = open('except.log', 'r')
            exceptiondata = f.read()
            exceptiondata = ubinascii.b2a_base64(exceptiondata)
            f.close()
            os.remove('except.log')
            content = b'sensorid=' + str(sensorid) + '&power=' + str(watt) + '&kwh_since_start=' + str(kwh_since_start) + '&exceptiondata=' + exceptiondata + '&password=' + passforsending
        else:
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
    except Exception as e:
        if debug:
            print(str(time.ticks_ms()) + ': Exception in senddata() happend. Returning')
        if exceptionlog:
            f = open('except.log', 'a')
            f.seek(0, 2)
            f.write('\n***** ' + str(time.ticks_ms()) + ' senddata() ***** ')
            sys.print_exception(e, f)
            f.close()
            if debug:
                print(str(time.ticks_ms()) + ': File except.log written')
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
    except Exception as e:
        if debug:
            print(str(time.ticks_ms()) + ': Exception in blinkarrived() happend. Returning')
        if exceptionlog:
            f = open('except.log', 'a')
            f.seek(0, 2)
            f.write('\n***** ' + str(time.ticks_ms()) + ' blinkarrived() ***** ')
            sys.print_exception(e, f)
            f.close()
            if debug:
                print(str(time.ticks_ms()) + ': File except.log written')
        return

# And now we are in main!
# Any exception will reset us
try:
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
        print(str(time.ticks_ms()) + ': impulses_per_kwh: ' + str(impulses_per_kwh))
        print(str(time.ticks_ms()) + ': Frequency is: ' + str(machine.freq()) + ' Hz')
    # Write the reset reason and startup config in except.log
    if exceptionlog:
        f = open('except.log', 'a')
        f.seek(0, 2)
        f.write('\n***** ' + str(time.ticks_ms()) + ' *****STARTUP***** ')
        f.write('\nReset reason: ' + str(machine.reset_cause()))
        f.write('\nsensorid: ' + str(sensorid))
        f.write('\nsendseconds: ' + str(sendseconds))
        f.write('\nsecondstrywificonnect: ' + str(secondstrywificonnect))
        f.write('\npinwithIRsensor: ' + str(pinwithIRsensor))
        f.write('\nwifiname: ' + str(wifiname))
        f.write('\nwifipass: ' + str(wifipass))
        f.write('\nserveraddress: ' + str(serveraddress))
        f.write('\npassforsending: ' + str(passforsending))
        f.write('\nimpulses_per_kwh: ' + str(impulses_per_kwh))
        f.write('\nFrequency is: ' + str(machine.freq()) + ' Hz')
        f.write('\n\n\n')
        f.close()
    # Activate a timer which will send our last sample every sendseconds Seconds
    if debug:
        print(str(time.ticks_ms()) + ': Activating Timer')
    tim = machine.Timer(-1)
    tim.init(period = sendseconds * 1000, mode = machine.Timer.PERIODIC, callback = senddata)
    # Activate a callback everytime we get a blink
    if debug:
        print(str(time.ticks_ms()) + ': Activating Interrupt')
    # We're using a hard Interrupt to be as fast as possible (Interrupts on ESP8266 are neither fast nor accurate, but good enough for our purpose)
    irsensor = machine.Pin(pinwithIRsensor, machine.Pin.IN)
    irsensor.irq(trigger = machine.Pin.IRQ_RISING, handler = blinkarrived, hard = True)
except Exception as e:
    if debug:
        print(str(time.ticks_ms()) + ': Exception in main() happend. RESTART')
    if exceptionlog:
        f = open('except.log', 'a')
        f.seek(0, 2)
        f.write('\n***** ' + str(time.ticks_ms()) + ' main() ***** ')
        sys.print_exception(e, f)
        f.close()
        if debug:
            print(str(time.ticks_ms()) + ': File except.log written')
    machine.reset()
