import asyncio
import json
import obd
import websockets

connection = obd.Async(fast=False, timeout=30)

connection.watch(obd.commands.RPM)

connection.start()

async def handler(websocket):
    async for message in websocket:
        print(f"\"{message}\" sent by user.")
        # await websocket.send(f"Your message is \"{message}\".")
        if message:
            print("Querying...")
            response = connection.query(obd.commands.RPM)
            print("The response:", response)

            rpm_data = response.value.magnitude
            message = json.dumps({"rpm": rpm_data})

            print("Should send the value now...")
            await websocket.send(message)

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())