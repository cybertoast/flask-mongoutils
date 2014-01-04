from flask_mongoutils import object_to_dict
from loader import db

class Author(db.Document):
    name = db.StringField()
    uri = db.StringField()
    password = db.StringField()
    excluded = db.StringField()

    # Fields to disallow from json responses
    _PRIVATE_FIELDS = ['password']

    def as_dict(self, **kwargs):
        resp = object_to_dict(self, exclude_fields=['excluded'], **kwargs)
        return resp

