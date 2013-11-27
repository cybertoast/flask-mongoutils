from __future__ import with_statement

import sys
import unittest

from flask import Flask, request, current_app
from flask_mongoutils import object_to_dict
from flask.ext.mongoengine import MongoEngine

if sys.version_info[0] < 3:
    b = lambda s: s
else:
    b = lambda s: s.encode('utf-8')

# Create mongodb instance
db = MongoEngine()

def create_app():
    # Create a sample application and go from there
    app = Flask(__name__)
    app.debug = True
    app.secret_key = '1234'
    app.config['MONGODB_DB'] = 'test_mongoutils' 
    app.config['MONGODB_HOST'] = 'localhost' 
    app.config['MONGODB_PORT'] = '27017' 
    db.init_app(app)
    return app

class Author(db.Document):
    name = db.StringField()
    uri = db.StringField()
    

class Book(db.Document):
    title = db.StringField()
    author = db.ReferenceField(Author)

    def as_dict(self, **kwargs):
        resp = object_to_dict(self, **kwargs)
        return resp

class ObjectToDictTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        author = Author(name="testauthor", uri="path/somewhere")
        author.save()
        book = Book(author=author, title='testbook')
        book.save()

    def tearDown(self):
        Author.drop_collection()
        Book.drop_collection()

    def test_dbref(self):
        with self.app.app_context():
            book = Book.objects().first()
            self.assertEqual('testbook', book.title)
            self.assertEqual('testauthor', book.author.name)

            resp = book.as_dict(app=current_app) 
            self.assertEqual('testauthor', resp.get('author').get('name'))

    def test_url_paths(self):
        asset_info = { 'ASSET_MODEL' : "Assets",
                       'ASSET_URL'   : 'http://localhost/_media/',
                       'ASSET_RESOURCE' : 'http://localhost/asset/'
                     }

        with self.app.app_context():
            book = Book.objects().first()
            self.assertEqual('testbook', book.title)
            self.assertEqual('testauthor', book.author.name)

            resp = book.as_dict(app=current_app, asset_info=asset_info, 
                                url_fields=['uri']) 
            self.assertEqual('testauthor', resp.get('author').get('name'))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ObjectToDictTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

