import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from flask import Flask, url_for
from app import create_app, db
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from app.models import Category

class CategoryRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()


    def test_add_category(self):
        logging.debug('Starting test for adding a new category.')
        response = self.client.post('/category/add_category', data={'name': 'New Category'}, follow_redirects=True)
        with self.app.app_context():
            category = Category.query.filter_by(name='New Category').first()
            logging.debug('New category created: %s', category.name)
            self.assertIsNotNone(category)

if __name__ == '__main__':
    unittest.main()
