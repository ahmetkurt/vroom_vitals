import asyncio
import logging
import obd
import websockets

HOST = ""
PORT = 8001
UPDATE_INTERVAL = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def read_and_send_rpm(connection, websocket):
    """ Continuously read RPM values from the OBD connection and send to WebSocket client. """
    while True:
        try:
            response = connection.query(obd.commands.RPM)
            rpm_value = response.value.magnitude if response.value else "N/A"
            await websocket.send(str(rpm_value))
            await asyncio.sleep(UPDATE_INTERVAL)
        except asyncio.CancelledError:
            logger.info("RPM reading task was cancelled.")
            break
        except Exception as e:
            logger.error(f"Error reading RPM: {e}")
            break

async def handle_client(websocket):
    """ Handle WebSocket connections and manage RPM reading tasks. """
    logger.info("New WebSocket connection established")

    try:
        connection = obd.OBD()
    except Exception as e:
        logger.error(f"Failed to initialize OBD connection: {e}")
        await websocket.close()
        return

    read_task = None

    try:
        async for message in websocket:
            logger.info(f"Received message from client: {message}")
            if message == "start":
                if read_task is None or read_task.done():
                    read_task = asyncio.create_task(read_and_send_rpm(connection, websocket))
                else:
                    logger.info("RPM reading task is already running.")
            elif message == "stop":
                if read_task:
                    read_task.cancel()
                    await websocket.send("RPM stream stopped")
                    read_task = None
                else:
                    logger.info("No RPM reading task to stop.")
            else:
                logger.warning(f"Unknown command: {message}")
    
    except websockets.ConnectionClosed:
        logger.info("WebSocket connection closed by the client")

    finally:
        if read_task:
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
        await connection.close()
        logger.info("OBD connection closed")

async def main():
    """ Main function to start the WebSocket server. """
    server = await websockets.serve(handle_client, HOST, PORT)
    logger.info(f"WebSocket server started on {HOST}:{PORT}")
    
    try:
        await asyncio.Future()
    finally:
        server.close()
        await server.wait_closed()
        logger.info("WebSocket server closed")

if __name__ == "__main__":
    asyncio.run(main())