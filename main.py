from pprint import pprint
from decoder import SignalDecoder
import RPi.GPIO as GPIO
from datetime import datetime
import time


try:
    import pydevd_pycharm
    pydevd_pycharm.settrace('patriks-macbook-pro.home', port=12321, stdoutToServer=True, stderrToServer=True)
    print("Running Debug Server...")
except (ImportError, ConnectionRefusedError):
    pass


def callback(channel):
    level = GPIO.input(channel)
    capture(level)


GPIO_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(GPIO_PIN, GPIO.BOTH, callback=callback)


decoder = SignalDecoder()


def capture(level):
    timecode = datetime.now().microsecond
    decoder.append(timecode, level)


if __name__ == '__main__':
    print("This is a simple decoder for raw data captured on GPIO pin " + str(GPIO_PIN))

    while True:
        time.sleep(5)
        decoder.decode()
        decoder.out()



