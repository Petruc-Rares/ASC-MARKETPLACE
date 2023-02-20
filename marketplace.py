"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import time
import unittest
import logging
from logging.handlers import RotatingFileHandler

from threading import Lock
from atomic_integer import AtomicInteger
from product import Tea, Coffee

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s:%(message)s')

handler = RotatingFileHandler('marketplace.log', maxBytes=1000000, backupCount=10)
formatter.converter = time.gmtime
handler.setFormatter(formatter)

logger.addHandler(handler)


class TestMarketplace(unittest.TestCase):
    """
    Class that represents the tests done for the class Marketplace
    """
    def setUp(self):
        self.queue_size_per_producer = 10
        self.marketplace = Marketplace(self.queue_size_per_producer)

    def test_register_producer(self):
        """
            tests marketplaces' register_producer method
        """
        for i in range(0, 50):
            producer_id = self.marketplace.register_producer()
            self.assertEqual(producer_id, i)

    def test_publish(self):
        """
            tests marketplaces' publish method
        """
        # all products should be published until the queue
        # maximum size is reached
        producer_id = self.marketplace.register_producer()
        product = Tea(name='TestTea', price=4, type='Herbal')

        for _ in range(1, self.queue_size_per_producer + 1):
            self.assertEqual(self.marketplace.publish(producer_id, product), True)

        for _ in range(1, self.queue_size_per_producer + 1):
            self.assertEqual(self.marketplace.publish(producer_id, product), False)

    def test_new_cart(self):
        """
            tests marketplaces' new_cart method
        """
        for i in range(0, 80):
            self.assertEqual(self.marketplace.new_cart(), i)

    def test_add_to_cart(self):
        """
            tests marketplaces' add_to_cart method
        """
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
        """
            tests marketplaces' remove_from_cart method
        """
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
        """
            tests marketplaces' test_place_order method
        """
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
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    """
    dictionary from producer_id to the semaphores used for the algorithm
    """
    available_products_pos = 0
    reserved_products_pos  = 1

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
        self.lock = Lock()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        # for each producer, we are going to add a semaphore, one that
        # stands for fullness and the other for emptyness
        id_producer = self.no_producers_registered.get_and_increment()

        self.info_producers[id_producer] = [[], []]

        logger.info(f"Producer with id: {id_producer} was registered")
        return id_producer

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """

        # critical section, as place_order might modify list at the same time
        self.lock.acquire()

        # check if the list of products for producer_id is full
        if len(self.info_producers[producer_id][self.available_products_pos]) \
         + len(self.info_producers[producer_id][self.reserved_products_pos])   \
                == self.queue_size_per_producer:
            logger.info(f"Producer with id:{producer_id} tried, but did not publish {product}")
            self.lock.release()
            return False

        self.info_producers[producer_id][self.available_products_pos].append(product)
        logger.info(f"Producer with id:{producer_id} published {product}")
        self.lock.release()
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        id_cart = self.no_last_cart.get_and_increment()

        self.info_carts[id_cart] = []

        logger.info(f"Cart with id {id_cart} was created")
        return id_cart

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """

        # check whether there is a producer that has the desired product
        self.lock.acquire()
        for producer_id, [list_products_available, _] in self.info_producers.items():
            if product in list_products_available:
                self.info_carts[cart_id].append((producer_id, product))
                self.info_producers[producer_id][self.available_products_pos].remove(product)
                self.info_producers[producer_id][self.reserved_products_pos].append(product)
                logger.info(f"{product} has been added to cart with id: {cart_id}")
                self.lock.release()
                return True

        # no producer has the desired product
        logger.info(f"{product} has NOT been added to cart with id: {cart_id}")
        self.lock.release()
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        self.lock.acquire()
        for (producer_id, key) in self.info_carts[cart_id]:
            if key == product:
                self.info_carts[cart_id].remove((producer_id, key))
                self.info_producers[producer_id][self.available_products_pos].append(product)
                self.info_producers[producer_id][self.reserved_products_pos].remove(product)
                logger.info(f"{product} was successfully removed from cart with id: {cart_id}")
                self.lock.release()
                return True

        logger.info(f"{product} was NOT removed from cart with id: {cart_id}")
        self.lock.release()
        return False

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """

        self.lock.acquire()

        for (producer_id, product) in self.info_carts[cart_id]:
            self.info_producers[producer_id][self.reserved_products_pos].remove(product)

        logger.info(f"cart with id {cart_id} has the products {self.info_carts[cart_id]}")

        self.lock.release()
        return self.info_carts[cart_id]

logging.shutdown()
