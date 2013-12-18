Features
========

Flask-Mongoutils provides the following helpers


Recursive Mongo Model to Dict/JSON
----------------------------------

The `object_to_dict` facility provides a mechism by which a Mongo (or really any)
object can be converted into a Dict output. This is needed in cases where you're
trying to return a jsoniy'ed response of a Mongo model.

