from quart import Quart, Response, render_template, stream_with_context
from pymata4 import pymata4
from .arduino_interface import Drive
from .system_info import generate_frames
from websockets.asyncio.server import serve

import asyncio
import json

# Create Quart app

app = Quart(__name__)

# initialize the arduino board

board = pymata4.Pymata4()  # auto-detects port (requires FirmataExpress)
driver = Drive(board)

async def relay_info(websocket):
    
    async for message in websocket:
        event = json.loads(message)
        receive_commands(event)


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
        async for frame in generate_frames():
            yield frame
    return Response(
        stream(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    )

async def main():
    async with serve(relay_info, "0.0.0.0", 8001):
        await app.run_task(host="0.0.0.0", port=5050)

if __name__ == "__main__":
    asyncio.run(main())
