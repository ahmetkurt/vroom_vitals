import obd

connection = obd.OBD()
print("Protocol ID", connection.protocol_id())
print("Protocol name", connection.protocol_name())
print("Supported commands", connection.supported_commands)

command = obd.commands.RPM

response = connection.query(command)
print("Response", response)
# Response
# Property	Description
# value	    The decoded value from the car
# command	The OBDCommand object that triggered this response
# message	The internal Message object containing the raw response from the car
# time	    Timestamp of response (as given by time.time())


# Module Layout
# obd.OBD            # main OBD connection class
# obd.Async          # asynchronous OBD connection class
# obd.commands       # command tables
# obd.Unit           # unit tables (a Pint UnitRegistry)
# obd.OBDStatus      # enum for connection status
# obd.scan_serial    # util function for manually scanning for OBD adapters
# obd.OBDCommand     # class for making your own OBD Commands
# obd.ECU            # enum for marking which ECU a command should listen to
# obd.logger         # the OBD module's root logger (for debug)