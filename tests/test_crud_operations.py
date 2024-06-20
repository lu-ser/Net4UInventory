import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from app import create_app, db
from app.models import Category, Location, Project, User, Product
from app.crud_operations import create_category, delete_category, update_category
from app.crud_operations import create_location, delete_location, update_location
from app.crud_operations import create_project, delete_project, update_project
from app.crud_operations import create_user, delete_user, update_user
from app.crud_operations import create_product, delete_product, update_product

class TestCRUDOperations(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
         # Creazione di Location e Project
        self.location = Location(pavilion="Main", room="101", cabinet="A1")
        self.project = Project(name="Important Project", funding_body="Big Funding")
        db.session.add(self.location)
        db.session.add(self.project)
        db.session.commit()

        # Creazione dell'utente
        self.user = create_user("test@example.com", "password", "user")
        db.session.add(self.user)
        db.session.commit()
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    ########################TEST USER #########################
    def test_create_user(self):
        """Testa la creazione di un nuovo utente."""
        user = create_user("test2@example.com", "password123", "admin")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test2@example.com")

    def test_update_user(self):
        """Testa l'aggiornamento di un utente esistente."""
        user = create_user("update@example.com", "password123", "user")
        updated_user = update_user(user.id, email="updated@example.com")
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, "updated@example.com")

    def test_delete_user(self):
        """Testa la cancellazione di un utente."""
        user = create_user("delete@example.com", "password123", "user")
        result = delete_user(user.id)
        self.assertTrue(result)
        self.assertIsNone(User.query.get(user.id))
    ################################################################
    ########################TEST PRODUCT #########################
    def test_create_product(self):
        """Testa la creazione di un nuovo prodotto."""
        product = create_product("Gadget", "U123", "A gadget", self.location.id, self.project.id, 10, self.user.id, [])
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Gadget")

    def test_update_product(self):
        """Testa l'aggiornamento di un prodotto esistente."""
        product = create_product("Device", "U124", "A device", self.location.id, self.project.id, 5, self.user.id, [])
        updated_product = update_product(product.id, name="Updated Device")
        self.assertIsNotNone(updated_product)
        self.assertEqual(updated_product.name, "Updated Device")

    def test_delete_product(self):
        """Testa la cancellazione di un prodotto."""
        product = create_product("Apparatus", "U125", "An apparatus", self.location.id, self.project.id, 20, self.user.id, [])
        result = delete_product(product.id)
        self.assertTrue(result)
        self.assertIsNone(Product.query.get(product.id))

if __name__ == '__main__':
    unittest.main(verbosity=2)
    