#!/usr/bin/python
# (C)opyright L.P.Klyne 2013
sw_topleft = 13
sw_topright = 7
sw_bottomleft = 12
sw_bottomright = 11
led_topleft = 22
led_topright = 18
led_bottomleft = 15
led_bottomright = 16

import logging
import os
import os.path
import time
import subprocess

import RPi.GPIO as GPIO
_log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(filename='example.log',level=logging.DEBUG)

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class led:
    def __init__(self, channel):
        self.channel = channel
        GPIO.setup(self.channel, GPIO.OUT, initial=GPIO.HIGH)
        self.pwm = GPIO.PWM(self.channel, 1)
        self.pwm.start(100.0)

    def flash(self, dc):
        _log.debug("flash led %s", self.channel)
        self.pwm.ChangeDutyCycle(dc)

    def on(self):
        _log.debug("led on %s", self.channel)
        self.pwm.ChangeDutyCycle(0.0)

    def off(self):
        _log.debug("led off %s", self.channel)
        self.pwm.ChangeDutyCycle(100.0)

    def is_on(self):
        return GPIO.input(self.channel)


class switch:
    def __init__(self, channel):
        self.channel = channel
        self.actions = []   # callable taking self
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def add_action(self, action):
        _log.debug("switch %s add action %s", self.channel, action)
        self.actions.append(action)
        if len(self.actions) == 1:
            GPIO.add_event_detect(
                self.channel, GPIO.BOTH,
                callback=lambda c: self.edge(), bouncetime=200)

    def remove_action(self, action):
        if len(self.actions) == 0:
            GPIO.remove_event_detect(self.channel)

    def edge(self):
        if self.is_on():
            for a in self.actions:
                _log.info("switch trigger %s action %s", self.channel, a)
                a(self)

    def is_on(self):
        return not GPIO.input(self.channel)  # pulled up


class disk:
    # States:
    # NotExist
    # ExistUnmounted
    # ExistsMounted
    def __init__(self, name, mount, led):
        self.devicename = name
        self.mountpoint = mount
        self.managed = False    # have we seen the device
        self.led = led

    def is_mounted(self):
        return os.path.ismount(self.mountpoint)

    def device_exists(self):
        return os.path.exists(self.devicename)

    def check_mount(self):
        # the aim here is to mount the disk when plugged in but to leave
        # unmounted when initiated by a switch and to mount when device
        # unplugged and plugged in again. I tried using udev but that
        # resulted in the disk mounting to early if plugged in at boot.
        if self.device_exists():
            if self.managed:
                #it is either allredy mounted or being unmounted
                pass
            else:
                _log.info("Disk added %s", self.devicename)
                if self.is_mounted():
                    self.led.on()
                else:
                    self.do_mount()
                self.managed = True
                return True

        elif self.managed:
            _log.info("Disk removed %s", self.devicename)
            self.managed = False

        return False

    def do_mount(self):
        self.led.flash(10)
        _log.info("Mounting %s on %s", self.devicename, self.mountpoint)
        subprocess.check_call(["mount", self.mountpoint])
        self.led.on()
        return True

    def do_unmount(self):
        if self.is_mounted():
            self.led.flash(50)
            _log.info("Un Mounting %s from %s", self.devicename, self.mountpoint)
            subprocess.check_call(["umount", self.mountpoint])
            self.led.off()
        return True


leds = [
    led(led_topleft),
    led(led_topright),
    led(led_bottomleft),
    led(led_bottomright)
]

switches = [
    switch(sw_topleft),
    switch(sw_topright),
    switch(sw_bottomleft),
    switch(sw_bottomright)
]

disks = [
    disk('/dev/sda1', '/mnt/diskA', leds[2]),
    disk('/dev/sdb1', '/mnt/diskB', leds[3]),
]


rsync_p = None


def do_rsync(scriptfile):
    global rsync_p
    if rsync_p is None and disks[0].is_mounted() and disks[1].is_mounted():
        _log.info("Rsync %s to/from %s using %s",
                  os.path.join(disks[1].mountpoint, "*"),
                  disks[0].mountpoint,
                  scriptfile)
        leds[1].flash(50)
        rsync_p = subprocess.Popen(scriptfile, shell=True)


def sync_a_to_b():
    do_rsync("/opt/fileserver/rsync_a_b.sh")


def sync_b_to_a():
    do_rsync("/opt/fileserver/rsync_b_a.sh")


def sync_both():
    do_rsync("/opt/fileserver/rsync_both.sh")


def do_shutdown():
    _log.info("Halt fileserver")
    subprocess.check_call(["halt"])


def main():
    global rsync_p
    leds[0].on()
    try:
        _log.info("Startup fileserver monitor")
        switches[0].add_action(lambda s: do_shutdown())
        switches[1].add_action(lambda s: sync_both())
        switches[2].add_action(lambda s: disks[0].do_unmount())
        switches[3].add_action(lambda s: disks[1].do_unmount())
        while(True):
            time.sleep(2.0)
            if rsync_p is None:
                if any([d.check_mount() for d in disks]):
                    sync_both()
            elif rsync_p.poll() is not None:    # has rsync completed
                rsync_p.returncode
                rsync_p = None
                leds[1].off()
    finally:
        leds[0].off()
        GPIO.cleanup()

main()
