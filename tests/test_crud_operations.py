import sys
import uuid
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from app import create_app, db
from app.models import Category, Location, Project, User, Product, Loan
from app.crud_operations import create_category, delete_category, update_category
from app.crud_operations import create_location, delete_location, update_location
from app.crud_operations import create_project, delete_project, update_project
from app.crud_operations import create_user, delete_user, update_user
from app.crud_operations import create_product, delete_product, update_product
from app.crud_operations import create_loan, delete_loan, update_loan
from app.crud_operations import add_manager_to_product, remove_manager_from_product
from datetime import datetime, timedelta

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

       # Creazione degli utenti
        unique_email_borrower = f"borrower{uuid.uuid4()}@example.com"
        self.borrower = create_user(unique_email_borrower, "password", "user")
        unique_email_manager = f"manager{uuid.uuid4()}@example.com"
        self.manager = create_user(unique_email_manager, "password", "manager")
        general_user_email = f"user{uuid.uuid4()}@example.com"
        self.user = create_user(general_user_email, "password", "user")

        db.session.add(self.borrower)
        db.session.add(self.manager)
        db.session.add(self.user)
        db.session.commit()

        # Creazione del prodotto con unique_code unico
        unique_product_code = f"P{uuid.uuid4()}"[:15]  # Assicurati che sia unico
        self.product = create_product("Widget", unique_product_code, "A useful widget", self.location.id, self.project.id, 10, self.borrower.id, [])
        db.session.add(self.product)
        db.session.commit()

        # Assegna gli oggetti come attributi di classe per l'accesso nei test
        self.borrower_id = self.borrower.id
        self.manager_id = self.manager.id
        self.product_id = self.product.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

# ########################TEST CATEGORIA #########################
    def test_create_category(self):
            """Test la creazione di una nuova categoria."""
            name = "Ricerca"
            category = create_category(name)
            self.assertIsNotNone(category)
            self.assertEqual(category.name, name)

    def test_update_category(self):
        """Test l'aggiornamento di una categoria esistente."""
        category = create_category("Iniziale")
        updated_category = update_category(category.id, "Aggiornata")
        self.assertIsNotNone(updated_category)
        self.assertEqual(updated_category.name, "Aggiornata")

    def test_delete_category(self):
        """Test l'eliminazione di una categoria."""
        category = create_category("Da eliminare")
        result = delete_category(category.id)
        self.assertTrue(result)
        self.assertIsNone(Category.query.get(category.id))


    ################################################################
    ########################TEST LOCATIONS #########################


    def test_create_location(self):
        # Crea una location
        location = create_location("Pavilion 1", "Room 101", "Cabinet A")
        self.assertIsNotNone(location)
        self.assertEqual(location.pavilion, "Pavilion 1")

    def test_update_location(self):
        # Aggiorna la location
        location = create_location("Pavilion 2", "Room 102", "Cabinet B")
        updated_location = update_location(location.id, cabinet="Cabinet C")
        self.assertIsNotNone(updated_location)
        self.assertEqual(updated_location.cabinet, "Cabinet C")

    def test_delete_location(self):
        # Elimina la location
        location = create_location("Pavilion da cancellare", "Room 101  da cancellare", "Cabinet A  da cancellare")
        result = delete_location(location.id)
        self.assertTrue(result)
        self.assertIsNone(Location.query.get(location.id))


    ################################################################
    ########################TEST Progetti #########################

        # Test per Progetto
    def test_create_update_and_delete_project(self):
        # Crea un progetto
        project = create_project("Nuova Ricerca", "Ente A")
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "Nuova Ricerca")

        # Aggiorna il progetto
        updated_project = update_project(project.id, funding_body="Ente B")
        self.assertIsNotNone(updated_project)
        self.assertEqual(updated_project.funding_body, "Ente B")

        # Elimina il progetto
        result = delete_project(project.id)
        self.assertTrue(result)
        self.assertIsNone(Project.query.get(project.id))
    def test_create_project(self):
        # Crea un progetto
        project = create_project("Nuova Ricerca", "Ente A")
        self.assertIsNotNone(project)
        self.assertEqual(project.name, "Nuova Ricerca")

    def test_update_project(self):
        # Aggiorna progetto
        project = create_project("Nuova Ricerca", "Ente B")
        updated_project = update_project(project.id, funding_body="Ente C")
        self.assertIsNotNone(updated_project)
        self.assertEqual(updated_project.funding_body, "Ente C")

    def test_delete_location(self):
        # Elimina la location
        project = create_project("Nuova Ricerca da cancellare", "Ente A da cancellare")
        result = delete_project(project.id)
        self.assertTrue(result)
        self.assertIsNone(Project.query.get(project.id))
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

    ################################################################
    ########################TEST LOAN #########################
    def test_add_manager_to_product(self):
        # Creazione e associazione di un manager a un prodotto
        manager = create_user("manager@example.com", "secure", "manager")
        product = create_product("Widget", "P101", "Useful Widget", self.location.id, self.project.id, 15, self.user.id, [])
        add_manager_to_product(product.id, manager.id)
        self.assertIn(manager, product.managers)

    def test_remove_manager_from_product(self):
        manager = create_user("manager@example.com", "secure", "manager")
        product = create_product("Widget", "P102", "Useful Widget", self.location.id, self.project.id, 15, self.user.id, [])
        add_manager_to_product(product.id, manager.id)
        remove_manager_from_product(product.id, manager.id)
        self.assertNotIn(manager, product.managers)

    def test_create_loan(self):
        """Testa la creazione di un prestito."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)  # Definire un end_date per il prestito
        loan = create_loan(
            product_id=self.product_id,
            borrower_id=self.borrower_id,
            manager_id=self.manager_id,
            start_date=start_date,
            end_date=end_date,
            status='pending'
        )
        self.assertIsNotNone(loan)
        self.assertEqual(loan.borrower_id, self.borrower_id)

    def test_update_loan(self):
        """Testa l'aggiornamento di un prestito."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        loan = create_loan(
            product_id=self.product.id,
            borrower_id=self.borrower.id,
            manager_id=self.manager.id,
            start_date=start_date,
            end_date=end_date
        )
        update_loan(loan.id, status='approved')
        self.assertEqual(loan.status, 'approved')

    def test_delete_loan(self):
        """Testa la cancellazione di un prestito."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        loan = create_loan(
            product_id=self.product.id,
            borrower_id=self.borrower.id,
            manager_id=self.manager.id,
            start_date=start_date,
            end_date=end_date
        )
        result = delete_loan(loan.id)
        self.assertTrue(result)
        self.assertIsNone(Loan.query.get(loan.id))

if __name__ == '__main__':
    unittest.main(verbosity=2)
    