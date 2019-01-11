import os
import sys
import time
import machine
import network
import usocket
import ubinascii
import micropython

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
# How many blinks does our power meter give per kWh
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
# We save our timestamp here to calculate the time between two blinks
messA = 0
messB = 0

# Exception in an ISR should be handled, reserve memory for that
micropython.alloc_emergency_exception_buf(100)

# This function is called everytime we get a pulse (Pin Change Interrupt)
def blinkarrived(pin):
    global messA
    global messB
    global totblinks
    totblinks = totblinks + 1
    if messA > messB:
        messB = time.ticks_ms()
    else:
        messA = time.ticks_ms()
    return

# This function will send our Data to the Internet
def senddata(timer):
    # Any exception will return
    try:
        global messA
        global messB
        global totblinks
        if messA == 0 or messB == 0:
            return
        # Check for overflow
        if abs(messA - messB) > 3600000:
            if messA > messB:
                messA = 0
            else:
                messB = 0
            return
        if messA > messB:
            timebetweenpulses = messA - messB
        else:
            timebetweenpulses = messB - messA
        # Calculate Watts
        watt = (36 * impulses_per_kwh) / timebetweenpulses
        # Calculate kWh since start
        kwh_since_start = totblinks / impulses_per_kwh
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
                if connectcount > secondstrywificonnect:
                    # We didn't connect after secondstrywificonnect seconds. Return for now
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
        addr_info = usocket.getaddrinfo(serveraddress, 80)
        addr = addr_info[0][-1]
        sock = usocket.socket()
        sock.connect(addr)
        sock.send(b'POST /tempsensor.php HTTP/1.1\r\n')
        sock.send(b'Host: ' + serveraddress + b'\r\n')
        sock.send(b'Content-Type: application/x-www-form-urlencoded\r\n')
        sock.send(b'Content-Length: ' + str(len(content)) + '\r\n')
        sock.send(b'\r\n')
        sock.send(content)
        sock.send(b'\r\n\r\n')
        sock.close()
        # Done
        messA = 0
        messB = 0
        return
    except Exception as e:
        if exceptionlog:
            f = open('except.log', 'a')
            f.seek(0, 2)
            f.write('\n***** ' + str(time.ticks_ms()) + ' senddata() ***** ')
            sys.print_exception(e, f)
            f.close()
        return

# And now we are in main!
# Any exception will reset us
try:
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
    tim = machine.Timer(-1)
    tim.init(period = sendseconds * 1000, mode = machine.Timer.PERIODIC, callback = senddata)
    # Activate a callback everytime we get a blink
    # We're using a Pin Change Interrupt, a hard one. To be as quick as possible.
    # Beware: The ISR can't allocate any memory and should be as short as possible!
    irsensor = machine.Pin(pinwithIRsensor, machine.Pin.IN)
    irsensor.irq(trigger = machine.Pin.IRQ_RISING, handler = blinkarrived, hard = True)
except Exception as e:
    if exceptionlog:
        f = open('except.log', 'a')
        f.seek(0, 2)
        f.write('\n***** ' + str(time.ticks_ms()) + ' main() ***** ')
        sys.print_exception(e, f)
        f.close()
    machine.reset()
