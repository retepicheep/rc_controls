import time
from pymata4 import pymata4


class Drive:
    """Used for driving the car."""

    # Pin definitions
    PIN_STBY = 3
    PIN_PWMA = 5
    PIN_AIN1 = 7
    PIN_PWMB = 6
    PIN_BIN1 = 8

    def __init__(self, board):
        self.board = board

        # Set pin modes
        board.set_pin_mode_digital_output(self.PIN_STBY)
        board.set_pin_mode_pwm_output(self.PIN_PWMA)
        board.set_pin_mode_digital_output(self.PIN_AIN1)
        board.set_pin_mode_pwm_output(self.PIN_PWMB)
        board.set_pin_mode_digital_output(self.PIN_BIN1)

    def _set_motors(self, left_speed: int, ain1: int, right_speed: int, bin1: int):
        self.board.digital_write(self.PIN_STBY, 1)
        self.board.pwm_write(self.PIN_PWMA, left_speed)
        self.board.digital_write(self.PIN_AIN1, ain1)
        self.board.pwm_write(self.PIN_PWMB, right_speed)
        self.board.digital_write(self.PIN_BIN1, bin1)

    def drive(self, direction: int, left_speed: int = 200, right_speed: int = 200):
        """Drive forward (1) or backward (-1)."""
        if direction not in (1, -1):
            print("Invalid direction: must be 1 (forward) or -1 (backward)")
            return
        d = 1 if direction == 1 else 0
        self._set_motors(left_speed, d, right_speed, d)

    def rotate(self, direction: int, left_speed: int = 200, right_speed: int = 200):
        """Rotate in place: 1 = right, -1 = left."""
        if direction not in (1, -1):
            print("Invalid direction: must be 1 (right) or -1 (left)")
            return
        d = 1 if direction == 1 else 0
        self._set_motors(left_speed, d, right_speed, 1 - d)  # BIN1 is opposite

    def stop(self):
        """Stop both motors."""
        self.board.digital_write(self.PIN_STBY, 0)
        self.board.pwm_write(self.PIN_PWMA, 0)
        self.board.digital_write(self.PIN_AIN1, 0)
        self.board.pwm_write(self.PIN_PWMB, 0)
        self.board.digital_write(self.PIN_BIN1, 0)


if __name__ == "__main__":
    board = pymata4.Pymata4()  # auto-detects port (requires FirmataExpress)
    drive = Drive(board)

    try:
        print("Forward...")
        drive.drive(1)
        time.sleep(5)
        drive.stop()

        print("Rotate right...")
        drive.rotate(1)
        time.sleep(5)
        drive.stop()

        print("Backward...")
        drive.drive(-1)
        time.sleep(5)
        drive.stop()

        print("Rotate left...")
        drive.rotate(-1)
        time.sleep(5)
        drive.stop()

    except KeyboardInterrupt:
        board.shutdown()