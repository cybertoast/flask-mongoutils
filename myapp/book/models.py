from loader import db
from flask_mongoutils import object_to_dict

class Book(db.Document):
    title = db.StringField()
    author = db.ReferenceField('Author')

    def as_dict(self, **kwargs):
        resp = object_to_dict(self, **kwargs)
        return resp

