from datetime import datetime
import sys
import uuid
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from app.services.business_logic import check_product_availability
from app import create_app, db
from app.models import Category, Location, Project, Loan
from app.crud.user_crud import create_user
from app.crud.product_crud import create_product


from datetime import datetime

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
        self.category1 = Category(name="Electronics")
        self.category2 = Category(name="Gadgets")
        db.session.add(self.category1)
        db.session.add(self.category2)
        db.session.commit()
        unique_product_code = f"P{uuid.uuid4()}"[:15]  # Assicurati che sia unico
        self.product = create_product("Widget", unique_product_code, "A useful widget", self.location.id, self.project.id, 10, self.borrower.id, [self.category1.id,self.category2.id])
        db.session.add(self.product)
        db.session.commit()
        self.loan1 = Loan(
        product_id=self.product.id,
        borrower_id=self.borrower.id,
        manager_id=self.manager.id,
        start_date=datetime(2023, 6, 1),
        end_date=datetime(2023, 6, 10),
        quantity=3,  # Assumi che 3 unità siano prestate
        status='approved'
    )
        self.loan2 = Loan(
            product_id=self.product.id,
            borrower_id=self.borrower.id,
            manager_id=self.manager.id,
            start_date=datetime(2023, 6, 5),
            end_date=datetime(2023, 6, 15),
            quantity=5,  # Assumi che altre 5 unità siano prestate
            status='approved'
        )
        db.session.add_all([self.loan1, self.loan2])
        db.session.commit()
        # Assegna gli oggetti come attributi di classe per l'accesso nei test
        self.borrower_id = self.borrower.id
        self.manager_id = self.manager.id
        self.product_id = self.product.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_availability_no_overlap(self):
        """Test availability when there is no overlap with existing loans."""
        is_available, available_quantity = check_product_availability(self.product.id, datetime(2023, 5, 20), datetime(2023, 5, 30))
        self.assertTrue(is_available)
        self.assertEqual(available_quantity, 5)

    def test_availability_partial_overlap(self):
        """Test availability when there is partial overlap with existing loans."""
        is_available, available_quantity = check_product_availability(self.product.id, datetime(2023, 6, 9), datetime(2023, 6, 20))
        self.assertTrue(is_available)
        self.assertEqual(available_quantity, 2)

    def test_availability_no_overlap(self):
        """Test availability when there is no overlap with existing loans."""
        is_available, available_quantity = check_product_availability(self.product.id, datetime(2023, 5, 20), datetime(2023, 5, 30))
        self.assertTrue(is_available)
        self.assertEqual(available_quantity, 10)


if __name__ == '__main__':
    unittest.main()