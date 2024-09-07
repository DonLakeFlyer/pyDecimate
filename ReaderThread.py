from CircularBuffer import *

import threading
import numpy
import sys
import logging

class ReaderThread(threading.Thread):
    def __init__ (self, bufferSize):
        super().__init__()
        self.bufferSize = bufferSize
        self.circularBuffer = CircularBuffer("Reader", bufferSize, np.csingle)

    def run(self):
        while True:
            bytes = sys.stdin.buffer.read(int(self.bufferSize / 4))
            logging.debug("Read %d bytes", len(bytes))
            buffer = numpy.frombuffer(bytes, dtype = numpy.csingle)
            self.circularBuffer.write(buffer)