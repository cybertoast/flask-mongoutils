from flask_mongoutils import object_to_dict
from loader import db

class Author(db.Document):
    name = db.StringField()
    uri = db.StringField()

