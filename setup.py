'''
    Flask-MongoUtils
    -------------------------

    Mongo tools and utilities, primarily for Flask apps, but could be for anything

'''
import os

from setuptools import setup

module_path = os.path.join(os.path.dirname(__file__), 'flask_mongoutils.py')
version_line = [line for line in open(module_path)
                if line.startswith('__version_info__')][0]

__version__ = '.'.join(eval(version_line.split('__version_info__ = ')[-1]))

setup(
    name='Flask-mongoutils',
    version=__version__,
    url='https://github.com/cybertoast/flask-mongoutils/',
    license='BSD',
    author='Sundar Raman',
    author_email='cybertoast@gmail.com',
    description='Some mongo helpers',
    long_description=__doc__,
    py_modules=['flask_mongoutils'],
    test_suite='test_mongoutils',
    zip_safe=False,
    platforms='any',
    install_requires=['Flask'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
