"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep

class Producer(Thread):
    """
    Class that represents a producer.
    """
    quantity_product_pos = 1
    wait_product_pos = 2

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        super().__init__(kwargs=kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time

    def run(self):
        # register to the marketplace
        id_producer = self.marketplace.register_producer()

        # try republishing
        while 1:
            # iterate through products
            for product in self.products:
                quantity_product = product[self.quantity_product_pos]
                time_production = product[self.wait_product_pos]
                sleep(time_production)
                for _ in range(1, quantity_product + 1):
                    # check if there is place to publish
                    while not self.marketplace.publish(id_producer, product[0]):
                        sleep(self.republish_wait_time)
