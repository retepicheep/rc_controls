from picamera2 import Picamera2
from simplejpeg import encode_jpeg


# Initialize and start the camera
camera = Picamera2()
camera.configure(camera.create_preview_configuration())
camera.start()


async def generate_frames():
    while True:
        frame = camera.capture_array()
        jpeg = encode_jpeg(frame, quality=85, colorspace="BGRA")
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
