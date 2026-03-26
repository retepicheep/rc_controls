from quart import Quart, Response, render_template, stream_with_context, session, redirect, url_for, request
from functools import wraps
from pymata4 import pymata4
from websockets.asyncio.server import serve
from .arduino_interface import Drive
from .video import generate_frames_async
from .system_health import return_sys_health
from .logger import setup_logger
import os
import asyncio
import json

ADMIN_USER = os.getenv("ROBOTCAR_USER")
ADMIN_PASS = os.getenv("ROBOTCAR_PASS")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# initiate logger

log = setup_logger(__name__, log_file="logs/app.log")

# Create Quart app

app = Quart(__name__)
app.config["RESPONSE_TIMEOUT"] = None  # disable timeout for streaming
log.info("Initialized Quart application.")

# initialize the arduino board

board = pymata4.Pymata4()  # auto-detects port (requires FirmataExpress)
driver = Drive(board)
last_cmds = None
log.info(f"Initilized board {board} and driver {driver}.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


async def relay_info(websocket):
    loop = asyncio.get_event_loop()
    log.info("Initialized async loop in relay_info().")

    async def health_push():
        while True:
            await asyncio.sleep(1.0)
            try:
                health = await loop.run_in_executor(None, return_sys_health)  # run blocking call off the event loop
                await websocket.send(health)
                log.info(f"Sent package {health} to the frontend.")
            except Exception as e:
                log.error(f"Failed to send package: {e}")
                break

    health_task = asyncio.create_task(health_push())
    log.info("Created async task for pushing system health data.")

    try:
        async for message in websocket:
            event = json.loads(message)
            receive_commands(event)
            log.info(f"Recieved commands from frontend: {event}")
    finally:
        health_task.cancel()

def receive_commands(cmds: list):
    global last_cmds
    cmds = set(cmds)

    if cmds == last_cmds:
        return
    last_cmds = cmds

    # Determine speed
    if "space" in cmds:
        speed = 100
        log.info(f"Space bar pressed, set speed to {speed}")
    elif "shift" in cmds:
        speed = 200
        log.info(f"Shift key pressed, set speed to {speed}")
    else:
        speed = 150
        log.info(f"No speed control key pressed, set speed to {speed}")

    # Full stop
    if "stop" in cmds:
        driver.stop()
        log.info("Stop command received, stopping vehicle.")
        return

    # Driving (forward/backward), with optional arc
    if "stop drive" not in cmds and ("w" in cmds or "s" in cmds):
        direction = 1 if "w" in cmds else -1
        left  = speed // 2 if "d" in cmds else speed
        right = speed // 2 if "a" in cmds else speed
        driver.drive(direction, left, right)
        log.info(
            f"Drive command sent: direction={'forward' if direction > 0 else 'backward'}, left={left}, right={right}"
                )
        return

    # Rotation (only when not driving)
    if "stop rotate" in cmds:
        driver.stop()
        log.info("Stop rotate command received, stopping vehicle.")
    else:
        if "a" in cmds:
            driver.rotate(1, speed, speed)
            log.info("Rotate left command sent.")
        elif "d" in cmds:
            driver.rotate(-1, speed, speed)
            log.info("Rotate right command sent.")
        else:
            driver.stop()
            log.info("No movement keys pressed, stopping vehicle.")

@app.route("/")
@login_required
async def home():
    return await render_template("home.html")

@app.route("/control")
@login_required
async def control():
    return await render_template("control.html")

@app.route("/login", methods=["GET", "POST"])
async def login():
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        password = form.get("password")

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["authenticated"] = True
            return redirect(url_for("home"))
        else:
            return await render_template("login.html", error="Invalid credentials")

    return await render_template("login.html")

@app.route("/video_feed")
@login_required
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
    log.info("Starting application.")
    asyncio.run(main())
    log.info("Shutting down application.\n-----------------------------------")
