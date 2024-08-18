import obd
import time

connection = obd.Async()
print("Protocol ID", connection.protocol_id())
print("Protocol name", connection.protocol_name())
print("Supported commands", connection.supported_commands)

command_rpm = obd.commands.RPM
connection.watch(command_rpm)
connection.start()

response = connection.query(command_rpm)
print("Response", response)

time.sleep(5)

with connection.paused() as was_running:
    print("Connection paused...")
    print("Was running?", was_running)

    command_throttle_pos = obd.commands.THROTTLE_POS
    connection.watch(command_throttle_pos)
    print("New command THROTTLE_POS has been subscribed...")

time.sleep(10)

with connection.paused() as was_running:
    print("Connection paused...")
    print("Was running?", was_running)

    connection.unwatch(command_rpm)
    print("Command RPM has been unsubscribed...")
