import numpy as np
import threading
import logging
import multiprocessing

class CircularBuffer:
    def __init__(self, name, capacity, dtype):
        self._name      = name
        self._capacity  = capacity
        self._dtype     = dtype
        self._buffer    = np.empty(capacity, dtype=dtype)
        self._readIndex = 0
        self._writeIndex = 0
        self._lock      = threading.Lock()
        self._itemCountCondition = multiprocessing.Condition()
        self._notifyItemCount    = 0
        logging.debug("CircularBuffer: %s: %d", self._name, self._capacity)

    def capacity(self):
        return self._capacity
    
    def registerItemCountCondition(self, itemCount):
        self._notifyItemCount = itemCount
        return self._itemCountCondition

    def _read(self, nElements: int, peek):
        retIndex  = 0
        headIndex = self._readIndex
        ret       = np.empty(nElements, dtype = self._dtype)

        while nElements:
            cBufferLeft = self._capacity - headIndex
            elementsToRead = min(nElements, cBufferLeft)
            ret[retIndex: retIndex + elementsToRead] = self._buffer[headIndex : headIndex + elementsToRead]
            nElements   -= elementsToRead
            retIndex    += elementsToRead
            headIndex   += elementsToRead
            if headIndex == self._capacity:
                headIndex = 0

        if not peek:
            self._readIndex = headIndex
        return ret    

    def read(self, nElements: int, overlap: int = 0):
        logging.debug("Reading samples from %s: readCount:unreadCount %d:%d", self._name, nElements, self.unreadCount())
        with self._lock:
            ret = np.empty(nElements, dtype = self._dtype)
            ret[:overlap] = self._read(overlap, True)
            nonOverlappedElements = nElements - overlap
            ret[overlap : overlap + nonOverlappedElements] = self._read(nonOverlappedElements, False)
        return ret

    def write(self, buffer):
        bufSize = len(buffer)
        logging.debug("Write: %s bufSize:read:write %d:%d:%d", self._name, bufSize, self._readIndex, self._writeIndex)
        with self._lock:
            if self._readIndex == self._writeIndex:
                roomLeft = self._capacity
            elif self._writeIndex > self._readIndex:
                roomLeft = self._writeIndex - self._readIndex
            else:
                # Buffer is wrapped around
                roomLeft = self._capacity - self._readIndex + self._writeIndex
            if bufSize > roomLeft:
                logging.warning("Buffer overflow: %s roomLeft:bufSize:read:write %d:%d:%d:%d", self._name, roomLeft, bufSize, self._readIndex, self._writeIndex)
                overflowCount = bufSize - roomLeft
                self._readIndex += overflowCount
                if self._readIndex >= self._capacity:
                    self._readIndex -= self._capacity
            bufIndex = 0
            while bufSize:
                cBufferLeft = self._capacity - self._writeIndex
                elementsToWrite = min(bufSize, cBufferLeft)
                self._buffer[self._writeIndex : self._writeIndex + elementsToWrite] = buffer[bufIndex : bufIndex + elementsToWrite]
                bufSize -= elementsToWrite
                bufIndex += elementsToWrite
                self._writeIndex += elementsToWrite
                if self._writeIndex == self._capacity:
                    self._writeIndex = 0
        if self._notifyItemCount and self.unreadCount() >= self._notifyItemCount:
            with self._itemCountCondition:
                self._itemCountCondition.notify()

    def reset(self):
        with self._lock:
            self._readIndex = 0
            self._writeIndex = 0

    def unreadCount(self):
        with self._lock:
            tailIndex = self._writeIndex
            if tailIndex < self._readIndex:
                tailIndex = self._capacity + tailIndex
            return tailIndex - self._readIndex
