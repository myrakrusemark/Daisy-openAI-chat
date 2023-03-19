import time
import RPi.GPIO as GPIO
import threading
import random

class RgbLed:
    description = "Provided LED patterns for visual status"

    def __init__(self, red_pin=11, green_pin=15, blue_pin=13):
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.blue_pin = blue_pin
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.red_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)
        GPIO.setup(self.blue_pin, GPIO.OUT)
        
        self.red_pwm = GPIO.PWM(self.red_pin, 100)
        self.green_pwm = GPIO.PWM(self.green_pin, 100)
        self.blue_pwm = GPIO.PWM(self.blue_pin, 100)
        
        self.red_running = False
        self.green_running = False
        self.blue_running = False
        
        self._threads = []
        self._stop_events = []


    def _create_thread(self, target, stop_event):
        t = threading.Thread(target=target)
        self._threads.append(t)
        self._stop_events.append(stop_event)
        t.start()

    def turn_on_color(self, red=0, green=0, blue=0):
        self.red_pwm.start(red)
        self.green_pwm.start(green)
        self.blue_pwm.start(blue)


    def blink_color(self, red=0, green=0, blue=0):
        stop_event = threading.Event()

        def blink(stop_event):
            while not stop_event.is_set():
                self.red_pwm.start(red)
                self.green_pwm.start(green)
                self.blue_pwm.start(blue)   
                start_time = time.monotonic()
                while time.monotonic() - start_time < 0.3:
                    pass
                self.red_pwm.stop()
                self.green_pwm.stop()
                self.blue_pwm.stop()
                start_time = time.monotonic()
                while time.monotonic() - start_time < 0.3:
                    pass

        self._create_thread(lambda: blink(stop_event), stop_event)
        return stop_event

    def breathe_color(self, red=0, green=0, blue=0):
        stop_event = threading.Event()

        def breathe(stop_event):
            self.red_pwm.start(0)
            self.green_pwm.start(0)
            self.blue_pwm.start(0)
            while not stop_event.is_set():
                for dutyCycle in range(0, 101, 5):
                    self.red_pwm.ChangeDutyCycle(dutyCycle * (red/100))
                    self.green_pwm.ChangeDutyCycle(dutyCycle * (green/100))
                    self.blue_pwm.ChangeDutyCycle(dutyCycle * (blue/100))
                    start_time = time.monotonic()
                    while time.monotonic() - start_time < 0.03:
                        pass
                for dutyCycle in range(100, -1, -5):
                    self.red_pwm.ChangeDutyCycle(dutyCycle * (red/100))
                    self.green_pwm.ChangeDutyCycle(dutyCycle * (green/100))
                    self.blue_pwm.ChangeDutyCycle(dutyCycle * (blue/100))
                    start_time = time.monotonic()
                    while time.monotonic() - start_time < 0.03:
                        pass
            self.red_pwm.stop()
            self.green_pwm.stop()
            self.blue_pwm.stop()

        self._create_thread(lambda: breathe(stop_event), stop_event)
        return stop_event


    def rainbow(self):
        stop_event = threading.Event()

        def rainbow_loop(stop_event):
            self.red_pwm.start(0)
            self.green_pwm.start(0)
            self.blue_pwm.start(0)
            while not stop_event.is_set():
                red = random.randint(0, 100)
                green = random.randint(0, 100)
                blue = random.randint(0, 100)
                self.turn_on_color(red, green, blue)
                start_time = time.monotonic()
                while time.monotonic() - start_time < 0.1:
                    pass

        self._create_thread(lambda: rainbow_loop(stop_event), stop_event)
        return stop_event



    def turn_all_off(self):
        for stop_event in self._stop_events:
            stop_event.set()
        for thread in self._threads:
            thread.join()
        self._threads = []
        self._stop_events = []
        self.red_pwm.stop()
        self.green_pwm.stop()
        self.blue_pwm.stop()
        
    def run(self):
        while True:
            print("""Ensure the following GPIO connections: R-11, G-15, B-13
            Colors: 1) White, 2) Yellow 3) Orange 4) Blink Orange 5) Breathe Green 6) Breathe Yellow, 7) Rainbow,
            8) Turn all off
            Use the format: color number""")
            cmd = input("-->")
            if cmd.isdigit():
                num = int(cmd)
                if num == 1:
                    self.turn_on_color(100,100,100)
                if num == 2:
                    self.turn_on_color(100,100,0)
                if num == 3:
                    self.turn_on_color(100,50,0)
                elif num == 4:
                    self.blink_color(100,50,0)
                elif num == 5:
                    self.breathe_color(0,100,0)
                elif num == 6:
                    self.breathe_color(100,100,0)
                elif num == 7:
                    self.rainbow()
                elif num == 8:
                    self.turn_all_off()
                else:
                    print("Not a valid color number")

            else:
                print("Not a valid command format")

