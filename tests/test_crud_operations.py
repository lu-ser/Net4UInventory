import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from app import create_app, db
from app.models import Category, Location, Project
from app.crud_operations import create_category, delete_category, update_category
from app.crud_operations import create_location, delete_location, update_location
from app.crud_operations import create_project, delete_project, update_project

class TestCRUDOperations(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


########################TEST CATEGORIA #########################
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

if __name__ == '__main__':
    unittest.main(verbosity=1)
    