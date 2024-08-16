import asyncio
import logging
import obd
import websockets
from typing import Dict
from enum import Enum

class Config:
    HOST = "0.0.0.0"
    PORT = 8001
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

semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_TASKS)

class TaskManager:
    """Manages asynchronous tasks for OBD data streaming."""
    def __init__(self, connection: obd.Async):
        self.connection = connection
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start_task(self, command_name: str, websocket: websockets.WebSocketClientProtocol):
        """Start monitoring a command and send data to the WebSocket client."""
        command = COMMAND_MAP.get(command_name)
        if command is None:
            await websocket.send(f"Unknown command: {command_name}")
            return

        if command_name in self.tasks and not self.tasks[command_name].done():
            await websocket.send(f"{command_name} task is already running.")
            return
        
        if len(self.tasks) >= Config.MAX_CONCURRENT_TASKS:
            await websocket.send("Too many concurrent tasks. Please stop some tasks before starting new ones.")
            return

        async def watch_command():
            async for response in self.connection.watch(command):
                if response is not None:
                    value = response.value.magnitude if response.value else "N/A"
                    await websocket.send(f"{command_name}: {value}")

        task = asyncio.create_task(watch_command())
        self.tasks[command_name] = task
        logger.info(f"Started {command_name} task.")
        await websocket.send(f"Started {command_name} task.")

    async def stop_task(self, command_name: str, websocket: websockets.WebSocketClientProtocol):
        """Stop monitoring a command and clean up the task."""
        if command_name in self.tasks:
            self.connection.unwatch(COMMAND_MAP[command_name])
            task = self.tasks.pop(command_name, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {command_name} was cancelled.")
                await websocket.send(f"Stopped {command_name} stream.")
            else:
                await websocket.send(f"No running task for {command_name}.")
        else:
            await websocket.send(f"No running task for {command_name}.")

    async def stop_all(self):
        """Stop all tasks and unwatch all commands."""
        self.connection.unwatch_all()
        for command_name, task in self.tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Task {command_name} was cancelled.")
        self.tasks.clear()

async def handle_client(websocket: websockets.WebSocketClientProtocol):
    """Handle WebSocket connections and manage reading tasks."""
    logger.info("New WebSocket connection established")
    connection = obd.Async()
    task_manager = TaskManager(connection)

    try:
        async for message in websocket:
            logger.info(f"Received message: {message}")

            parts = message.strip().lower().split()
            if len(parts) != 2:
                await websocket.send("Invalid command format. Use 'start <command>' or 'stop <command>'.")
                continue

            action, command_name = parts

            if action == "start":
                await task_manager.start_task(command_name, websocket)
            elif action == "stop":
                await task_manager.stop_task(command_name, websocket)
            else:
                await websocket.send("Unknown action. Use 'start <command>' or 'stop <command>'.")

    except websockets.ConnectionClosed:
        logger.info("WebSocket connection closed by client")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handling: {e}")

    finally:
        await task_manager.stop_all()
        connection.close()
        logger.info("OBD connection closed")

async def main():
    """Main function to start the WebSocket server."""
    async with websockets.serve(handle_client, Config.HOST, Config.PORT):
        logger.info(f"WebSocket server started on {Config.HOST}:{Config.PORT}")
        try:
            await asyncio.Future()
        finally:
            logger.info("WebSocket server is shutting down.")

if __name__ == "__main__":
    asyncio.run(main())