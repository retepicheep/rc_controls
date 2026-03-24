from quart import Quart, Response, render_template, stream_with_context
from pymata4 import pymata4
from websockets.asyncio.server import serve
from .arduino_interface import Drive
from .video import generate_frames_async
from .system_health import return_sys_health

import asyncio
import json

# Create Quart app

app = Quart(__name__)
app.config["RESPONSE_TIMEOUT"] = None  # disable timeout for streaming

# initialize the arduino board

board = pymata4.Pymata4()  # auto-detects port (requires FirmataExpress)
driver = Drive(board)

async def relay_info(websocket):
    loop = asyncio.get_event_loop()

    async def health_push():
        while True:
            await asyncio.sleep(1.0)
            try:
                health = await loop.run_in_executor(None, return_sys_health)  # run blocking call off the event loop
                await websocket.send(health)
            except Exception:
                break

    health_task = asyncio.create_task(health_push())
    try:
        async for message in websocket:
            event = json.loads(message)
            receive_commands(event)
    finally:
        health_task.cancel()
    



def receive_commands(cmds: list):
    cmds = set(cmds)

    # Determine speed
    if "space" in cmds:
        speed = 100
    elif "shift" in cmds:
        speed = 200
    else:
        speed = 150

    # Full stop
    if "stop" in cmds:
        driver.stop()
        return

    # Individual stop commands
    if "stop drive" in cmds:
        driver.stop()

    if "stop rotate" in cmds:
        driver.stop()

    # Driving (forward/backward), with optional arc
    if "stop drive" not in cmds:
        if "w" in cmds or "s" in cmds:
            direction = 1 if "w" in cmds else -1
            left  = speed // 2 if "d" in cmds else speed
            right = speed // 2 if "a" in cmds else speed
            driver.drive(direction, left, right)
            return

    # Rotation (only when not driving)
    if "stop rotate" not in cmds:
        if "a" in cmds:
            driver.rotate(1, speed, speed)
        elif "d" in cmds:
            driver.rotate(-1, speed, speed)

@app.route("/control")
async def control():
    return await render_template("control.html")

@app.route("/video_feed")
async def video_feed():
    @stream_with_context
    async def stream():
        async for frame in generate_frames_async():
            yield frame
    return Response(
        stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",  # add this
        }
    )

async def main():
    async with serve(relay_info, "0.0.0.0", 8001):
        await app.run_task(host="0.0.0.0", port=5050)

if __name__ == "__main__":
    asyncio.run(main())
