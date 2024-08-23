import obd
import time

# def rpm_callback(r):
#     if not r.is_null():
#         print(f"RPM: {r.value} RPM")
#     else:
#         print("RPM: No data")

# def pos_callback(r):
#     if not r.is_null():
#         print(f"POS: {r.value} POS")
#     else:
#         print("POS: No data")

# def bar_callback(r):
#     if not r.is_null():
#         print(f"BAR: {r.value} BAR")
#     else:
#         print("BAR: No data")

# def speed_callback(s):
#     if not s.is_null():
#         print(f"Speed: {s.value} km/h")
#     else:
#         print("Speed: No data")

# connection = obd.Async(fast=False, timeout=30)

# connection.watch(obd.commands.RPM, callback=rpm_callback)
# connection.watch(obd.commands.SPEED, callback=speed_callback)

# connection.start()

# time.sleep(5)

# with connection.paused() as was_running:
#     print("Connection paused...")
#     print("Was running?", was_running)

#     connection.watch(obd.commands.THROTTLE_POS, callback=pos_callback)
#     print("New command THROTTLE_POS has been subscribed...")

# time.sleep(10)

# with connection.paused() as was_running:
#     print("Connection paused...")
#     print("Was running?", was_running)

#     connection.unwatch(obd.commands.RPM, callback=rpm_callback)
#     print("Command RPM has been unsubscribed...")

# time.sleep(15)

# with connection.paused() as was_running:
#     print("Connection paused...")
#     print("Was running?", was_running)

#     connection.watch(obd.commands.BAROMETRIC_PRESSURE, callback=bar_callback)
#     print("New command BAROMETRIC_PRESSURE has been subscribed...")

# try:
#     while True:
#         # The main loop can do other things, or just pass
#         pass

# except KeyboardInterrupt:
#     print("Stopped by user")
# finally:
#     connection.stop()  # Stop the async connection

################################################################

connection = obd.Async(fast=False, timeout=30)

connection.watch(obd.commands.RPM)

connection.start()

print(connection.query(obd.commands.RPM))