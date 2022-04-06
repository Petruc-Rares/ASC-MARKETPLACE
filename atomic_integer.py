"""
This module represents the atomic_integer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Lock

class AtomicInteger:
    """
    Class that holds an integer and does
    atomic operations on the integer
    """
    def __init__(self, number=0):
        """
        Constructor

        :type number: Int
        :param number: the initial value for the atomic integer
        """
        self.number = number
        self.my_lock = Lock()

    def get_and_increment(self):
        """
        Returns the atomic integer incremented
        """
        with self.my_lock:
            aux = self.number
            self.number = self.number + 1
        return aux
