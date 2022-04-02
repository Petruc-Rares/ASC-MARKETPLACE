"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import unittest

# TODO: will test the functioning
# of all methods defined by Marketplace
# if other methods will be added, tests will
# be added as well
from tema.atomicInteger import AtomicInteger
from threading import Semaphore


class TestMarketplace(unittest.TestCase):
    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')


class Marketplace:
    """
    dictionary from producer_id to the semaphores used for the algorithm
    """

    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    empty_semaphore_pos = 0
    available_coffees_pos = 1
    available_teas_pos = 2

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.no_producers_registered = AtomicInteger()
        self.no_last_cart = AtomicInteger()
        self.info_producers = {}
        self.info_carts = {}

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        # for each producer, we are going to add a semaphore, one that
        # marks whether new items can be produced
        # the second one that holds info about the number of coffees
        # available and the third one that holds the number of teas
        # available
        self.info_producers[self.no_producers_registered.getNumber()] = [
            Semaphore(value=self.queue_size_per_producer),
            Semaphore(value=0),
            Semaphore(value=0)]
        return self.no_producers_registered.getAndIncrement()

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """

        result_acquire = self.info_producers[producer_id][self.empty_semaphore_pos].acquire(timeout=0.1)
        if not(result_acquire):
            self.info_producers[producer_id][self.empty_semaphore_pos].release()
            return result_acquire
        if product.__class__.__name__ == 'Coffee':
            self.info_producers[producer_id][self.available_coffees_pos].release()
        if product.__class__.__name__ == 'Tea':
            self.info_producers[producer_id][self.available_teas_pos].release()

        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        self.info_carts[self.no_last_cart.getNumber()] = []
        return self.no_last_cart.getAndIncrement()

    def get_sem_position(self, product):
        if (product.__class__.__name__ == 'Coffee'):
            look_for_pos = self.available_coffees_pos
        elif (product.__class__.__name__ == 'Tea'):
            look_for_pos = self.available_teas_pos
        return look_for_pos

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        look_for_pos = self.get_sem_position(product)

        for product_id, semaphores in self.info_producers.items():
            result_acquire = semaphores[look_for_pos].acquire(timeout=0.1)
            if not result_acquire:
                semaphores[look_for_pos].release()
                return False
            else:
                # the producer with product_id can produce again
                self.info_producers[product_id][self.empty_semaphore_pos].release()
                self.info_carts[cart_id].append((product_id, product))
                return True

        # no producer has the desired product
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        look_for_position = self.get_sem_position(product)

        for (product_id, key) in self.info_carts[cart_id]:
            #print(product_id, key)
            if key == product:
                self.info_carts[cart_id].remove((product_id, key))
                # remove one available product offered by product_id
                self.info_producers[product_id][look_for_position].release()
                # determine producer not to produce other stuff, as there are still
                # unsold items; fails if producer already can't produce other stuff
                self.info_producers[product_id][self.empty_semaphore_pos].acquire(timeout=0.1)
                break

    def print_semaphores(self, product_id):
        print(f"cat poate produce: {self.info_producers[product_id][self.empty_semaphore_pos]._value}")
        print(f"cat ceai e disponibil: {self.info_producers[product_id][self.available_teas_pos]._value}")
        print(f"cata cafea e disponibila: {self.info_producers[product_id][self.available_coffees_pos]._value}")

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        for (prod_id, product) in self.info_carts[cart_id]:
            self.info_producers[prod_id][self.empty_semaphore_pos].release()


        return self.info_carts[cart_id]
