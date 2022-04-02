from threading import Lock


class AtomicInteger:
    def __init__(self, number=0):
        self.number = number
        self.my_lock = Lock()

    def getAndIncrement(self):
        with self.my_lock:
            self.number = self.number + 1
        return self.number - 1

    def getNumber(self):
        return self.number
