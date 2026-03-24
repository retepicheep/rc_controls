from picamera2 import Picamera2
from simplejpeg import encode_jpeg
import asyncio
from concurrent.futures import ThreadPoolExecutor

camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()

_camera_executor = ThreadPoolExecutor(max_workers=1)  # dedicated thread for camera

async def generate_frames_async():
    loop = asyncio.get_event_loop()
    while True:
        frame = await loop.run_in_executor(_camera_executor, camera.capture_array)
        jpeg = encode_jpeg(frame, quality=85, colorspace="BGRA")
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
        await asyncio.sleep(0.033)