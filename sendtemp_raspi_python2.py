!/usr/bin/python
import time
import serial
import bme280
import requests

temperature,pressure,humidity = bme280.readBME280All()

# Read CO2 from MH-Z19
ser = serial.Serial('/dev/serial0', 9600)
write = ser.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
co2 = ser.read(9)
time.sleep(1)
co2 = ord(co2[2])*256 + ord(co2[3])

print "Temperature : ", temperature, "C"
print "Pressure : ", pressure, "hPa"
print "Humidity : ", humidity, "%"
print "CO2 : ", co2

r = requests.post("http://www.myserver.de/tempsensor.php", data={'sensorid': 1, 'temp': temperature, 'press': pressure, 'hum': humidity, 'co2': co2, 'password': '3'}, timeout = 50)

print r.text

