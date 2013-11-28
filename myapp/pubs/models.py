from flask_mongoutils import object_to_dict
from loader import db

class Publisher(db.Document):
    name = db.StringField()

