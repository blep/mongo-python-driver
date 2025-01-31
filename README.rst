========
PyMongo3
========
:Info: See `the mongo site <http://www.mongodb.org>`_ for more information. See `github <http://github.com/mongodb/mongo-python-driver/tree>`_ for the latest source.

About
=====

This is an unofficial port of PyMongo 2.0 to Python 3.1 or later.
gridfs and its tests are not ported yet! bson and pymongo are working.

The PyMongo distribution contains tools for interacting with MongoDB
database from Python.  The ``bson`` package is an implementation of
the `BSON format <http://bsonspec.org>`_ for Python. The ``pymongo``
package is a native Python driver for MongoDB. The ``gridfs`` package
is a `gridfs
<http://www.mongodb.org/display/DOCS/GridFS+Specification>`_
implementation on top of ``pymongo``.

Issues / Questions / Feedback
=============================

Any issues with, questions about, or feedback for PyMongo should be
sent to the mongodb-user list on Google Groups. For confirmed issues
or feature requests, open a case on `jira
<http://jira.mongodb.org>`_. Please do not e-mail any of the PyMongo
developers directly with issues or questions - you're more likely to
get an answer on the list.

Installation
============

You can download the project source and do **python
setup.py install** to install.

Dependencies
============

PyMongo3 needs Python 3.x where x >= 1.

Additional dependencies are:

- (to generate documentation) sphinx_
- (to auto-discover tests) `nose <http://somethingaboutorange.com/mrl/projects/nose/>`_

Examples
========
Here's a basic example (for more see the *examples* section of the docs):

>>> import pymongo
>>> connection = pymongo.Connection("localhost", 27017)
>>> db = connection.test
>>> db.name
'test'
>>> db.my_collection
Collection(Database(Connection('localhost', 27017), 'test'), 'my_collection')
>>> db.my_collection.save({"x": 10})
ObjectId('4aba15ebe23f6b53b0000000')
>>> db.my_collection.save({"x": 8})
ObjectId('4aba160ee23f6b543e000000')
>>> db.my_collection.save({"x": 11})
ObjectId('4aba160ee23f6b543e000002')
>>> db.my_collection.find_one()
{'x': 10, '_id': ObjectId('4aba15ebe23f6b53b0000000')}
>>> for item in db.my_collection.find():
...     print(item["x"])
...
10
8
11
>>> db.my_collection.create_index("x")
'x_1'
>>> for item in db.my_collection.find().sort("x", pymongo.ASCENDING):
...     print(item["x"])
...
8
10
11
>>> [item["x"] for item in db.my_collection.find().limit(2).skip(1)]
[8, 11]

Documentation
=============

You will need sphinx_ installed to generate the
documentation. Documentation can be generated by running **python
setup.py doc**. Generated documentation can be found in the
*doc/build/html/* directory.

Testing
=======

The easiest way to run the tests is to install `nose
<http://somethingaboutorange.com/mrl/projects/nose/>`_ (**easy_install
nose**) and run **nosetests** or **python setup.py test** in the root
of the distribution. Tests are located in the *test/* directory.

.. _sphinx: http://sphinx.pocoo.org/
