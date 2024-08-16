import asyncio
import logging
import obd
import websockets
from typing import Dict, Union
from enum import Enum

HOST = "0.0.0.0"
PORT = 8001
UPDATE_INTERVAL = 1
COMMAND_TIMEOUT = 10
MAX_CONCURRENT_TASKS = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommandType(Enum):
    RPM = "rpm"
    SPEED = "speed"

COMMAND_MAP: Dict[str, obd.OBDCommand] = {
    CommandType.RPM.value: obd.commands.RPM,
    CommandType.SPEED.value: obd.commands.SPEED,
}

semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def query_obd_command(connection: obd.OBD, command: obd.OBDCommand) -> Union[str, float]:
    """Query the OBD-II command with retry logic for transient errors."""
    try:
        response = await asyncio.wait_for(connection.query(command), timeout=COMMAND_TIMEOUT)
        return response.value.magnitude if response.value else "N/A"
    except (asyncio.TimeoutError, Exception) as e:
        logger.error(f"Failed to query {command.name}: {e}")
        return "Error"

async def read_and_send_data(connection: obd.OBD, websocket: websockets.WebSocketClientProtocol, command: obd.OBDCommand):
    """Continuously read and send data based on the command."""
    while True:
        async with semaphore:
            value = await query_obd_command(connection, command)
            await websocket.send(f"{command.name}: {value}")
            await asyncio.sleep(UPDATE_INTERVAL)

async def handle_client(websocket: websockets.WebSocketClientProtocol):
    """Handle WebSocket connections and manage reading tasks."""
    logger.info("New WebSocket connection established")

    try:
        connection = obd.OBD()
    except Exception as e:
        logger.error(f"Failed to initialize OBD connection: {e}")
        await websocket.send("Failed to initialize OBD connection.")
        await websocket.close()
        return

    tasks: Dict[str, asyncio.Task] = {}

    try:
        async for message in websocket:
            logger.info(f"Received message: {message}")

            parts = message.strip().lower().split()
            if len(parts) != 2:
                await websocket.send("Invalid command format. Use 'start <command>' or 'stop <command>'.")
                continue

            action, command_name = parts
            command = COMMAND_MAP.get(command_name)

            if command is None:
                await websocket.send(f"Unknown command: {command_name}")
                continue

            if action == "start":
                if command_name not in tasks or tasks[command_name].done():
                    if len(tasks) >= MAX_CONCURRENT_TASKS:
                        await websocket.send("Too many concurrent tasks. Please stop some tasks before starting new ones.")
                        continue
                    tasks[command_name] = asyncio.create_task(read_and_send_data(connection, websocket, command))
                    logger.info(f"Started {command_name} task.")
                else:
                    await websocket.send(f"{command_name} task is already running.")
            elif action == "stop":
                if command_name in tasks:
                    tasks[command_name].cancel()
                    await websocket.send(f"{command_name} stream stopped")
                    del tasks[command_name]
                    logger.info(f"Stopped {command_name} task.")
                else:
                    await websocket.send(f"No running task for {command_name}.")
            else:
                await websocket.send("Unknown action. Use 'start <command>' or 'stop <command>'.")

    except websockets.ConnectionClosed:
        logger.info("WebSocket connection closed by client")

    finally:
        for task in tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Task was cancelled.")

        try:
            connection.close()
        except Exception as e:
            logger.error(f"Error closing OBD connection: {e}")
        logger.info("OBD connection closed")

async def main():
    """Main function to start the WebSocket server."""
    async with websockets.serve(handle_client, HOST, PORT):
        logger.info(f"WebSocket server started on {HOST}:{PORT}")
        try:
            await asyncio.Future()
        finally:
            logger.info("WebSocket server is shutting down.")

if __name__ == "__main__":
    asyncio.run(main())
