from __future__ import with_statement

import sys
import unittest

from flask import Flask, request, current_app
from loader import db
from myapp.author.models import Author
from myapp.book.models import Book

if sys.version_info[0] < 3:
    b = lambda s: s
else:
    b = lambda s: s.encode('utf-8')

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


class ObjectToDictTestCase(unittest.TestCase):
    # class Publisher(db.Document):
    #     name = db.StringField()

    def setUp(self):
        #from nose.tools import set_trace; set_trace()
        self.app = create_app()
        self.app.name = 'myapp'
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

            resp = book.as_dict(app=current_app, recursive=True, depth=4) 
            self.assertEqual('testauthor', resp.get('author').get('name'))

    def test_url_paths(self):
        asset_info = { 'ASSET_MODEL' : "Assets",
                       'ASSET_URL'   : 'http://localhost/_media/',
                       'ASSET_RESOURCE' : 'http://localhost/asset/'
                     }

        with self.app.app_context():
            book = Book.objects().first()

            resp = book.as_dict(app=current_app, asset_info=asset_info, 
                                uri_fields=['uri'], recursive=True, depth=4) 
            self.assertTrue(resp.get('author').get('uri').startswith(asset_info.get('ASSET_URL')))

    def test_model_map(self):
        model_map = {'Publisher': 'authors'}
        # Do some sketchy stuff
        # with self.app.app_context():
        #     publisher = Publisher.objects().first()
        #     resp = publisher.as_dict(app=current_app, model_map=model_map)
        #     self.assertEqual('testpublisher', resp.get('publisher').get('name'))
        self.fail("Not implemented")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ObjectToDictTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

