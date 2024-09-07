from ReaderThread import *

import time
import logging
import numpy
from scipy import signal
from socket import *

def pyDecimate():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s |  %(filename)s:%(lineno)d')

    samplesPerDecimation  = 1024 * 5

    reader = ReaderThread(samplesPerDecimation * 2)
    reader.start()

    notifyDecimationCondition = reader.circularBuffer.registerItemCountCondition(samplesPerDecimation)

    udpSendSocket = socket(AF_INET, SOCK_DGRAM)

    while True:
        with notifyDecimationCondition:
            while reader.circularBuffer.unreadCount() < samplesPerDecimation:
                logging.debug("Waiting for samples: unreadCount: %d", reader.circularBuffer.unreadCount())
                notifyDecimationCondition.wait()
        decimatedBuffer = reader.circularBuffer.read(samplesPerDecimation)
        decimatedSamples = signal.decimate(decimatedBuffer, 8, ftype='fir')
        logging.debug("Decimated samples: %d", decimatedSamples.size)
        udpSendSocket.sendto(decimatedSamples.tobytes(), ("127.0.0.1", 10000))

if __name__ == '__main__':
    pyDecimate()