import time
from multiprocessing import Process, Queue
from decoder import SignalDecoder
from database import DatabaseConnector
from datetime import datetime
import RPi.GPIO as GPIO
import argparse


GPIO_PIN = 23
REMOTE_DEBUG_HOST = "patriks-macbook-pro.home"
REMOTE_DEBUG_PORT = 12321


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-g", "--gpio", help="GPIO Pin (BCM) for 433Mhz-Sensor")
parser.add_argument("-o", "--host", help="Host for remote debugging session")
parser.add_argument("-p", "--port", help="Port for remote debugging session")

# Read command line arguments
args = parser.parse_args()

if args.gpio:
    GPIO_PIN = args.gpio
if args.host:
    REMOTE_DEBUG_PORT = args.port
if args.port:
    REMOTE_DEBUG_HOST = args.host


try:
    # Try to connect to remote debugging instance (if server is listening)
    import pydevd_pycharm
    pydevd_pycharm.settrace(
        REMOTE_DEBUG_HOST,
        port=REMOTE_DEBUG_PORT,
        stdoutToServer=True,
        stderrToServer=True)
except (ImportError, ConnectionRefusedError):
    # We won't do anything here, just run local if the server is not listening
    pass


def callback(channel):
    # Callback for GPIO event detection
    level = GPIO.input(channel)
    timestamp = datetime.now().microsecond
    mq.put([timestamp, level])


def setup_callback(cb):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(GPIO_PIN, GPIO.BOTH, callback=cb)


def start_decoder(qq, dba):
    reader_process = Process(target=SignalDecoder, args=(qq, dba))
    reader_process.daemon = True
    reader_process.start()

    return reader_process


if __name__ == '__main__':
    print("This is a simple decoder for raw data captured on GPIO pin " + str(GPIO_PIN))

    mq = Queue()
    db = DatabaseConnector()

    setup_callback(callback)

    decoder_process = start_decoder(mq, db)
    decoder_process.join()

    while True:
        time.sleep(1)

