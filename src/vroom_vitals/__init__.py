import obd

connection = obd.OBD() # auto-connects to USB or RF port

cmd = obd.commands.SPEED # select an OBD command (sensor)

response = connection.query(cmd) # send the command, and parse the response

print('++++++++++++++++++++++++++++++++')
print("Ports", obd.scan_serial()) # ['/dev/ttyUSB0', '/dev/ttyUSB1']
print("Is connected?", connection.is_connected())
print("Port name", connection.port_name())
print("Protocol ID", connection.protocol_id())
print("Protocol name", connection.protocol_name())
print("Connection status", connection.status())
print('===============================')
print(response.value) # returns unit-bearing values thanks to Pint
print(response.value.to("kph")) # user-friendly unit conversions
print(response.value.to("mph")) # user-friendly unit conversions