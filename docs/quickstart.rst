Quick Start
===========

-  `Basic MongoEngine Application <#basic-mongoengine-application>`_

Basic MongoEngine Application
==============================

It's best to look at the test_mongoutils.py file and the test application "myapp".

MongoEngine Install requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ mkvirtualenv <your-app-name>
    $ pip install -e git+https://github.com/cybertoast/flask-mongoutils@0.2.0#egg=Flask-Mongoutils-dev


MongoEngine Application
~~~~~~~~~~~~~~~~~~~~~~~

The following code sample illustrates how to get started as quickly as
possible using MongoEngine:

::

    from flask_mongoengine import MongoEngine
    from flask_mongoutils import object_to_dict 

    # Create app
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'super-secret'

    # MongoDB Config
    app.config['MONGODB_DB'] = 'mydatabase'
    app.config['MONGODB_HOST'] = 'localhost'
    app.config['MONGODB_PORT'] = 27017

    # Create database connection object
    db = MongoEngine(app)

    class Book(db.Document):
        title = db.StringField()
        author = db.ReferenceField('Author')
        publisher = db.ReferenceField('Publisher')

        def as_dict(self, **kwargs):
            resp = object_to_dict(self, **kwargs)
            return resp

    # Views
    @app.route('/')
    def home():
        book = Book.objects().first()
        resp = book.as_dict(app=app, recursive=True, depth=4)

        return jsonify(data=resp)

    if __name__ == '__main__':
        app.run()

