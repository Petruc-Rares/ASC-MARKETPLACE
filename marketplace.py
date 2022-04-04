"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

import unittest
#import logging
#from logging.handlers import RotatingFileHandler

from threading import Semaphore, Lock
from tema.atomicInteger import AtomicInteger
from tema.product import Tea, Coffee

#logging.shutdown()
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)

#formatter = logging.Formatter('%(asctime)s:%(message)s')

#handler = RotatingFileHandler('marketplace.log', maxBytes=10000, backupCount=10)
#handler.setLevel(logging.INFO)
#formatter.converter = time.gmtime()
#handler.setFormatter(formatter)

#logger.addHandler(handler)


class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.queue_size_per_producer = 10
        self.marketplace = Marketplace(self.queue_size_per_producer)

    def test_register_producer(self):
        for i in range(0, 50):
            producer_id = self.marketplace.register_producer()
            self.assertEqual(producer_id, i)

    def test_publish(self):
        # all products should be published until the queue
        # maximum size is reached
        producer_id = self.marketplace.register_producer()
        product = Tea(name='TestTea', price=4, type='Herbal')

        for _ in range(1, self.queue_size_per_producer + 1):
            self.assertEqual(self.marketplace.publish(producer_id, product), True)

        for _ in range(1, self.queue_size_per_producer + 1):
            self.assertEqual(self.marketplace.publish(producer_id, product), False)

    def test_new_cart(self):
        for i in range(0, 80):
            self.assertEqual(self.marketplace.new_cart(), i)

    def test_get_sem_position(self):
        product_tea = Tea(name='TestTea', price=4, type='Herbal')
        product_coffee = Coffee(name='TestCoffee', price=5,
                                acidity='test_acidity',
                                roast_level='test_roast_level')

        self.assertEqual(self.marketplace.get_sem_position(product_tea),
                        self.marketplace.available_teas_pos)

        self.assertEqual(self.marketplace.get_sem_position(product_coffee),
                        self.marketplace.available_coffees_pos)

    def test_add_to_cart(self):
        # try to add to cart something not published/available
        cart1 = self.marketplace.new_cart()
        product_tea = Tea(name='NonExistingTea', price=4, type='Herbal')
        self.assertEqual(self.marketplace.add_to_cart(cart1, product_tea), False)

        # try to add to cart something that is available
        cart2 = self.marketplace.new_cart()
        product_coffee = Coffee(name='ExistingCoffee', price=5,
                                acidity='test_acidity',
                                roast_level='test_roast_level')
        producer_id = self.marketplace.register_producer()
        self.marketplace.publish(producer_id, product_coffee)
        self.assertEqual(self.marketplace.add_to_cart(cart2, product_coffee), True)

    def test_remove_from_cart(self):
        # try to delete something inexistent from cart
        cart1 = self.marketplace.new_cart()
        product_tea = Tea(name='ExistingTea', price=4, type='Herbal')
        self.assertEqual(self.marketplace.remove_from_cart(cart1, product_tea), False)

        # try to delete something that exists
        cart2 = self.marketplace.new_cart()
        product_coffee = Coffee(name='ExistingCoffee', price=5,
                                acidity='test_acidity',
                                roast_level='test_roast_level')

        producer_id = self.marketplace.register_producer()
        self.marketplace.publish(producer_id, product_coffee)

        self.marketplace.add_to_cart(cart2, product_coffee)
        self.assertEqual(self.marketplace.remove_from_cart(cart2, product_coffee), True)

    def test_place_order(self):
        cart = self.marketplace.new_cart()
        product_tea = Tea(name='ExistingTea', price=4, type='Herbal')
        product_coffee = Coffee(name='ExistingCoffee', price=5,
                                acidity='test_acidity',
                                roast_level='test_roast_level')
        producer_id = self.marketplace.register_producer()

        self.marketplace.publish(producer_id, product_coffee)
        self.marketplace.publish(producer_id, product_coffee)
        self.marketplace.publish(producer_id, product_tea)
        self.marketplace.publish(producer_id, product_tea)

        self.marketplace.add_to_cart(cart, product_coffee)
        self.marketplace.add_to_cart(cart, product_coffee)
        self.marketplace.add_to_cart(cart, product_tea)
        self.marketplace.remove_from_cart(cart, product_coffee)

        self.assertListEqual(self.marketplace.place_order(cart),
                             [(producer_id, product_coffee), (producer_id, product_tea)])


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
        self.lock = Lock()
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

        #logger.info(f"A producer was registered with id:
        #  {self.no_producers_registered.getNumber()}")
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

        if not result_acquire:
            #logger.info(f"Producer with id:{producer_id} tried, but did not publish {product}")
            return False
        if product.__class__.__name__ == 'Coffee':
            self.info_producers[producer_id][self.available_coffees_pos].release()
        if product.__class__.__name__ == 'Tea':
            self.info_producers[producer_id][self.available_teas_pos].release()

        #logger.info(f"Producer with id:{producer_id} published {product}")

        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        self.info_carts[self.no_last_cart.getNumber()] = []

        #logger.info(f"Cart with id {self.no_last_cart.getNumber()} was created")
        return self.no_last_cart.getAndIncrement()

    def get_sem_position(self, product):
        """
        Gets the position for product

        :type product: Product
        :param product: product

        :returns an int representing the semaphore position
        """
        if product.__class__.__name__ == 'Coffee':
            look_for_pos = self.available_coffees_pos
        elif product.__class__.__name__ == 'Tea':
            look_for_pos = self.available_teas_pos
        #logger.info(f"For product: {product}, position to look at semaphores is {look_for_pos}")
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
            # print(f'inainte de not {look_for_pos} pt {product_id}')
            # self.print_semaphores(product_id)
            result_acquire = semaphores[look_for_pos].acquire(timeout=0.1)
            if result_acquire:
                self.info_carts[cart_id].append((product_id, product))
                #logger.info(f"{product} has been added to cart with id: {cart_id}")
                return True

        # no producer has the desired product
        #logger.info(f"{product} has NOT been added to cart with id: {cart_id}")
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
            if key == product:
                self.info_carts[cart_id].remove((product_id, key))
                # remove one available product offered by product_id
                self.info_producers[product_id][look_for_position].release()
                #logger.info(f"{product} was successfully removed from cart with id: {cart_id}")
                return True

        #logger.info(f"{product} was NOT removed from cart with id: {cart_id}")
        return False

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        for (prod_id, _) in self.info_carts[cart_id]:
            self.info_producers[prod_id][self.empty_semaphore_pos].release()

        #logger.info(f"cart with id {cart_id} has the products {self.info_carts[cart_id]}")
        return self.info_carts[cart_id]
