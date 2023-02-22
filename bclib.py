#!/usr/bin/env python3

import serial
import logging
from time import sleep

class barCodeReader(object):
    def __init__(self, port = '/dev/ttyACM0', timeout=1) -> None:
        self.port = port
        self.timeout=timeout
        self.running = False
        self._serial = None
        self._prev_errno = None
    def start(self):
        try:
            self._serial = serial.Serial(port=self.port,timeout=self.timeout)
            self.running = True
        except serial.SerialException as e:
            self.running = False
            if self._prev_errno != e.args[0]:
                logging.error(e)
                self._prev_errno = e.args[0]

    def next(self):
        try:
            bc = self._serial.readline().decode('ascii').rstrip('\r\n')
            return(bc)
        except serial.SerialException as e:
            self.running=False
            logging.error("{}:{}".format(self.port,e))
            return(None)
def main():
    b=barCodeReader(port = '/dev/ttyACM0', timeout=1)
    b.start()
    logging.info(b.running)
    while not b.running:
        print('*',)
        sleep(1)
        b.start()

#    while b.running:
#        bc = b.next()
#        if bc is not None:
#            if len(bc)>0:
#                print(bc)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)
    main()
