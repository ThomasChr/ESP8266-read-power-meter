# Using parts of the following scripts:
# 1. https://www.raspberrypi-spy.co.uk/2016/07/using-bme280-i2c-temperature-pressure-sensor-in-python/
# 2. http://ecorov.com/2017/08/03/i2c-gy-91.html
import time
import ustruct
import machine
import network
import usocket

# Globals
debug = 1
sensorid = 4
sensoraddr = 0x76
sendseconds = 60
secondstrywificonnect = 10
REG_DATA = 0xF7
REG_CONTROL = 0xF4
REG_CONFIG = 0xF5
REG_CONTROL_HUM = 0xF2
REG_HUM_MSB = 0xFD
REG_HUM_LSB = 0xFE
OVERSAMPLE_TEMP = 2
OVERSAMPLE_PRES = 2
MODE = 1


def senddata(timer):
    try:
        wdt.feed()
        if debug:
            print(str(time.ticks_ms()) + ': Trying to connect')
        # Connect to WiFi -> Get interfaces
        sta_if = network.WLAN(network.STA_IF)
        ap_if = network.WLAN(network.AP_IF)
        # Deactivate access point, we're station only
        ap_if.active(False)
        # Now connect
        connectcount = 0
        if not sta_if.isconnected():
            sta_if.active(True)
            sta_if.connect('1', '2')
            while not sta_if.isconnected():
                connectcount = connectcount + 1
                time.sleep(1)
                if debug:
                    print(str(time.ticks_ms()) + ': Connect try: ' + str(connectcount))
                if connectcount > secondstrywificonnect:
                    # We didn't connect after secondstrywificonnect seconds. Let's sleep
                    if debug:
                        print(str(time.ticks_ms()) + ': Connect failed after ' + str(
                            connectcount) + ' seconds sleep. Going to deepsleep')
                    machine.deepsleep()

        # Startup I2C
        if debug:
            print(str(time.ticks_ms()) + ': Starting I2C')
        i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21), freq=100000)

        # Set Oversampling
        if debug:
            print(str(time.ticks_ms()) + ': Setting BME280 Oversampling')
        OVERSAMPLE_HUM = 2
        i2c.writeto_mem(sensoraddr, REG_CONTROL_HUM, bytearray([OVERSAMPLE_HUM]))
        control = OVERSAMPLE_TEMP << 5 | OVERSAMPLE_PRES << 2 | MODE
        i2c.writeto_mem(sensoraddr, REG_CONTROL, bytearray([control]))

        # Read Calibration data from sensor
        if debug:
            print(str(time.ticks_ms()) + ': Getting BME280 Calibration data')
        cal1 = i2c.readfrom_mem(sensoraddr, 0x88, 24)
        cal2 = i2c.readfrom_mem(sensoraddr, 0xA1, 1)
        cal3 = i2c.readfrom_mem(sensoraddr, 0xE1, 7)

        # Convert bytes to words
        dig_T1 = ustruct.unpack('H', cal1[0:2])[0]
        dig_T2 = ustruct.unpack('h', cal1[2:4])[0]
        dig_T3 = ustruct.unpack('h', cal1[4:6])[0]
        dig_P1 = ustruct.unpack('H', cal1[6:8])[0]
        dig_P2 = ustruct.unpack('h', cal1[8:10])[0]
        dig_P3 = ustruct.unpack('h', cal1[10:12])[0]
        dig_P4 = ustruct.unpack('h', cal1[12:14])[0]
        dig_P5 = ustruct.unpack('h', cal1[14:16])[0]
        dig_P6 = ustruct.unpack('h', cal1[16:18])[0]
        dig_P7 = ustruct.unpack('h', cal1[18:20])[0]
        dig_P8 = ustruct.unpack('h', cal1[20:22])[0]
        dig_P9 = ustruct.unpack('h', cal1[22:24])[0]
        dig_H1 = ustruct.unpack('B', cal2[0:1])[0]
        dig_H2 = ustruct.unpack('h', cal3[0:2])[0]
        dig_H3 = ustruct.unpack('B', cal3[2:3])[0]
        dig_H4 = ustruct.unpack('b', cal3[3:4])[0]
        dig_H4 = (dig_H4 << 24) >> 20
        dig_H4 = dig_H4 | (ustruct.unpack('b', cal3[4:5])[0] & 0x0F)
        dig_H5 = ustruct.unpack('b', cal3[5:6])[0]
        dig_H5 = (dig_H5 << 24) >> 20
        dig_H5 = dig_H5 | (ustruct.unpack('B', cal3[4:5])[0] >> 4 & 0x0F)
        dig_H6 = ustruct.unpack('b', cal3[6:7])[0]

        # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
        if debug:
            print(str(time.ticks_ms()) + ': Sleeping for BME280 to be ready')
        wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + (
                    (2.3 * OVERSAMPLE_HUM) + 0.575)
        time.sleep(wait_time / 1000)

        # Read temperature/pressure/humidity
        if debug:
            print(str(time.ticks_ms()) + ': Reading BME280')
        data = i2c.readfrom_mem(sensoraddr, REG_DATA, 8)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]

        # Refine temperature
        if debug:
            print(str(time.ticks_ms()) + ': Refine temperature')
        var1 = ((((temp_raw >> 3) - (dig_T1 << 1))) * (dig_T2)) >> 11
        var2 = (((((temp_raw >> 4) - (dig_T1)) * ((temp_raw >> 4) - (dig_T1))) >> 12) * (dig_T3)) >> 14
        t_fine = var1 + var2
        temperature = float(((t_fine * 5) + 128) >> 8)

        # Refine pressure and adjust for temperature
        if debug:
            print(str(time.ticks_ms()) + ': Refine pressure')
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * dig_P6 / 32768.0
        var2 = var2 + var1 * dig_P5 * 2.0
        var2 = var2 / 4.0 + dig_P4 * 65536.0
        var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * dig_P1
        if var1 == 0:
            pressure = 0
        else:
            pressure = 1048576.0 - pres_raw
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * dig_P8 / 32768.0
            pressure = pressure + (var1 + var2 + dig_P7) / 16.0

        # Refine humidity
        if debug:
            print(str(time.ticks_ms()) + ': Refine humidity')
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (dig_H4 * 64.0 + dig_H5 / 16384.0 * humidity)) * (
                    dig_H2 / 65536.0 * (1.0 + dig_H6 / 67108864.0 * humidity * (1.0 + dig_H3 / 67108864.0 * humidity)))
        humidity = humidity * (1.0 - dig_H1 * humidity / 524288.0)
        if humidity > 100:
            humidity = 100
        elif humidity < 0:
            humidity = 0

        # Data is ready
        temperature = temperature / 100.0
        pressure = pressure / 100.0
        humidity = humidity
        if debug:
            print(str(time.ticks_ms()) + ': Data fetched: temp ' + str(temperature) + ' - press ' + str(
                pressure) + ' - hum ' + str(humidity))

        # Get CO2 Sensor Data (MH-Z19)
        uart = machine.UART(2, 9600)
        uart.init(9600, bits=8, parity=None, stop=1)
        uart.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
        time.sleep(1)
        co2 = uart.read(9)
        co2 = co2[2] * 256 + co2[3]
        print('co2: ' + str(co2))

        # Send data to the Internet, a Post Request with http - we don't use SSL here!
        content = b'sensorid=' + str(sensorid) + '&temp=' + str(temperature) + '&press=' + str(
            pressure) + '&hum=' + str(humidity) + '&co2=' + str(co2) + '&password=3'

        if debug:
            print(str(time.ticks_ms()) + ': Connecting to website')
        addr_info = usocket.getaddrinfo("myserver.de", 80)
        addr = addr_info[0][-1]
        sock = usocket.socket()
        sock.connect(addr)
        sock.send(b'POST /tempsensor.php HTTP/1.1\r\n')
        sock.send(b'Host: myserver.de\r\n')
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
        return
    except:
        if debug:
            print(str(time.ticks_ms()) + ': Exception happend. RESET')
        machine.reset()


if debug:
    print(str(time.ticks_ms()) + ': ***STARTUP***')
    print(str(time.ticks_ms()) + ': sensorid: ' + str(sensorid))
    print(str(time.ticks_ms()) + ': sensoraddr: ' + str(sensoraddr))
    print(str(time.ticks_ms()) + ': sendseconds: ' + str(sendseconds))
    print(str(time.ticks_ms()) + ': secondstrywificonnect: ' + str(secondstrywificonnect))
    print(str(time.ticks_ms()) + ': REG_DATA: ' + str(REG_DATA))
    print(str(time.ticks_ms()) + ': REG_CONTROL: ' + str(REG_CONTROL))
    print(str(time.ticks_ms()) + ': REG_CONFIG: ' + str(REG_CONFIG))
    print(str(time.ticks_ms()) + ': REG_CONTROL_HUM: ' + str(REG_CONTROL_HUM))
    print(str(time.ticks_ms()) + ': REG_HUM_MSB: ' + str(REG_HUM_MSB))
    print(str(time.ticks_ms()) + ': REG_HUM_LSB: ' + str(REG_HUM_LSB))
    print(str(time.ticks_ms()) + ': OVERSAMPLE_TEMP: ' + str(OVERSAMPLE_TEMP))
    print(str(time.ticks_ms()) + ': OVERSAMPLE_PRES: ' + str(OVERSAMPLE_PRES))
    print(str(time.ticks_ms()) + ': MODE: ' + str(MODE))

# Activate Watchdog
if debug:
	print(str(time.ticks_ms()) + ': Activating Watchdog with 120 seconds')
wdt = machine.WDT(timeout = 120000)
wdt.feed()

# Activate a send timer
if debug:
    print(str(time.ticks_ms()) + ': Activating Timer')
tim = machine.Timer(-1)
tim.init(period=sendseconds * 1000, mode=machine.Timer.PERIODIC, callback=senddata)