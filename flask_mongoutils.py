# -*- coding: utf-8 -*-

"""
    :copyright: (c) 2011 Sundar Raman, all rights reserved
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

__version_info__ = ('0', '3', '16')
__version__ = '.'.join(__version_info__)
__author__ = 'Sundar Raman'
__license__ = 'BSD'
__copyright__ = '(c) 2013 by Sundar Raman'
__all__ = ['MongoUtils']

import re

# -*- coding: utf-8 -*-
from itertools import groupby
from mongoengine import Document, EmbeddedDocument
from mongoengine.queryset import QuerySet
from numbers import Number
from types import ModuleType
import bson
import os
import re
from datetime import datetime

def object_to_dict(obj=None, recursive=False, depth=1, **kwargs):
    """Take a Mongo (or other) object and return a JSON
     
    Kwargs:
        obj (bson/json): Object to convert into a dictionary
        exclude_nulls (bool): Whether to include keys with null values in return data
        recursive: Descend into the referenced documents and return those objects.
            Keep in mind that recursive can be problematic since there's no depth!
        depth (int): recursion-depth. If 0, this is unlimited!
    
        app (Flask-app): Required. Current flask app
        use_derefs (bool): whether to use deref_only and deref_exclude properties 
            to filter dereferenced values. See doc in EntityMixin
        query_function (dict): Name of the method on the model to use instead of 'objects'
            {'with_field_having_count': {'field-name': 'count'}}
        deep_filter (dict): Filter to apply on a nested model
            {'model-name': {filter} }
        exclude_fields: List of fields to exclude/remove all the way down
        asset_info (dict): Info for converting relative `uri_fields` to absolute paths
            {'ASSET_RESOURCE': 'http://localhost/assets/',
             'ASSET_URL': 'http://localhost/_media/'}
        types_as_str_repr (List): List of types that should be treated as their __str__
            representation. For example, Assets might need to be just a URL rather than
            the resolved object in certain cases.
        uri_fields (list): List of fieldnames to convert to full-path
            These are the fields that should be treated as URLs, and should be prefixed
            with asset_info.ASSET_RESOURCE

        model_map (dict): The mapping between a model class and the path where it is defined
            This allows non-standard (ie. not module.models.py) mapping.
            Defined as {'ModelName': 'path.to.model'} where `path.to.model` is the full path 
            under your project to the .py file containing the model definition.
            E.g. `{ 'Creators': 'path.to.model' }` would be the same as:
                `from <current_project_name>.path.to.model import Creators`
            See the lazy_load function below for an implementation example.
        current_depth (int): Internal. Stores internal recursion state.

    Returns:
        Dictionary version of the provided object
    
    KNOWN ISSUES:
        The use of 'types_as_str_repr' and a list of uri-fields seems to not 
        work correctly with asset-prefixing.
        In this case the type is prefixed correctly for the str'ed type, but is 
        not prepended to deeply string fields. 
    """
    # Some fixed values. Keep in mind that these can't be globals since the
    # app context is not available
    if not 'app' in kwargs.keys():
        raise Exception("Object Encoder expects to receive 'app' as a flask instance (flask.current_app")
    app = kwargs.get('app')

    asset_info = kwargs.get('asset_info') or {}
    # If resource-path is provided then use that, otherwise the url-path
    # TODO: Should the caller have a different expectation based on which value is
    #   sent? Why bother having a dict, rather than a single ASSET_PREFIX value?
    ASSET_URL = asset_info.get('ASSET_RESOURCE') or asset_info.get('ASSET_URL') or ''

    if (  kwargs.get('current_depth') is not None and
          kwargs.get('current_depth') > 0 and
          kwargs.get('current_depth') >= depth and 
          recursive is True ):
        recursive = False
    else:
        if kwargs.get('current_depth') is None: 
            kwargs['current_depth'] = 0
        kwargs['current_depth'] = kwargs.get('current_depth') + 1

    # Dynamic keys to pass up the recursion stack
    if kwargs.get('delete_keys') is None: 
        kwargs['delete_keys'] = []
      
    if obj is None:
        return obj
    
    if isinstance(obj, (Document, EmbeddedDocument)):
        # This may not be very portable, so need to figure out a bit more configurable
        # solution for other projects
        if kwargs.get('types_as_str_repr') and obj.__class__.__name__ in kwargs.get('types_as_str_repr'):
            out = str(obj)
            # out = os.path.join(asset_info.get('ASSET_RESOURCE'), str(obj))
            return out
        
        out = dict(obj._data)
        _private_fields = getattr(obj, '_PRIVATE_FIELDS', None)
        for k,v in out.items():
            if kwargs.get('exclude_fields') and k in kwargs.get('exclude_fields'):
                out[k] = None
                kwargs['delete_keys'].append(k)
                continue
            if k in ['_PRIVATE_FIELDS']:
                out[k] = None
                kwargs['delete_keys'].append(k)
                continue
            if _private_fields and k in _private_fields:
                out[k] = None
                kwargs['delete_keys'].append(k)
                continue
            
            if v is None and kwargs.get('exclude_nulls'):
                out.pop(k)
                continue
            
            # Apply the URL absolute path prefix for the defined fields
            if kwargs.get('uri_fields') and k in kwargs.get('uri_fields'):
                kwargs['apply_url_prefix'] = True
            else:
                kwargs['apply_url_prefix'] = False
                
            if isinstance(v, bson.ObjectId):
                if k is None:
                    out['id'] = str(v)
                    kwargs['delete_keys'].append(k)
                else:
                    # Unlikely since ObjectId's key is always None
                    out[k] = str(v)
            else:
                # No further processing necessary for some values
                if v is None and kwargs.get('exclude_nulls'):
                    out.pop(k)
                    kwargs['delete_keys'].append(k)
                    continue
                
                else:
                    if isinstance(v, (str, unicode)):
                        out[k] = v
                    elif isinstance(v, Number):
                        out[k] = v
                    else:
                        out[k] = object_to_dict(v, recursive=recursive, 
                                                depth=depth, **kwargs)

            # We've already established that this key should be asset-prefixed (above)
            # But we do this prefixing last so that we can handle types_as_str_repr()
            # conversions
            if isinstance(out[k], (str, unicode)):
                if (kwargs.get('apply_url_prefix') and asset_info):
                    if not out[k].startswith(ASSET_URL) and k in kwargs.get('uri_fields'):
                        out[k] = "%s%s" % (ASSET_URL, out[k])
                        
            if ( kwargs.get('types_as_str_repr') and 
                 obj.__class__.__name__ in kwargs.get('types_as_str_repr') and
                 kwargs.get('apply_url_prefix') and asset_info):
                if isinstance(out[k], list):
                    out[k] = ["%s%s" % (ASSET_URL, item) if not item.startswith(ASSET_URL) else item
                              for item in out[k] 
                              if item and isinstance(item, (str, unicode))]
                elif isinstance(out[k], dict):
                    for field in kwargs.get('uri_fields'):
                        if isinstance(out[k].get(field), (str, unicode)):
                            if out[k].get(field) and not out[k][field].startswith(ASSET_URL): 
                                out[k][field] = "%s%s" % (ASSET_URL, out[k][field])
            
        # To avoid breaking loop flow, do at the end of looping
        for delkey in kwargs.get('delete_keys'):
            # double check that we're not deleting a non-empty key
            if ( delkey in out.keys() and 
                 ((out.get(delkey) is None) or (delkey is None)) ):
                out.pop(delkey)
                
        # Remove our tracker for the next loop
        if kwargs.get('delete_keys'): kwargs['delete_keys'] = []
                    
    elif isinstance(obj, QuerySet):
        out = [object_to_dict(item, recursive=recursive, depth=depth, **kwargs) 
               for item in obj]
    elif isinstance(obj, ModuleType):
        out = None
    elif isinstance(obj, groupby):
        out = [ (g,list(l)) for g,l in obj ]
    elif isinstance(obj, (list)):
        # GeoPointField is also a list!
        out = []
        for item in obj:
            odict = object_to_dict(item, recursive=recursive, depth=depth, **kwargs)
            # Don't return null objects that were transformed, since this would 
            # generally mean an orphaned record
            if isinstance(item, bson.DBRef) and not odict: 
                continue
            out.append(odict)
        kwargs['current_depth'] -= 1

    elif isinstance(obj, (dict)):
        out = {}
        for k,v in obj.items():
            if kwargs.get('exclude_fields') and k in kwargs.get('exclude_fields'):
                obj[k] = None
                kwargs['delete_keys'].append(k)
                continue

            if k in kwargs.get('delete_keys'):
                obj[k] = None
            if k in kwargs.get('uri_fields'):
                kwargs['apply_url_prefix'] = True
            else:
                kwargs['apply_url_prefix'] = False
            vout = object_to_dict(v, recursive=recursive, depth=depth, **kwargs)

            if ( v is None and 
                 kwargs.get('exclude_nulls')):                
                # Don't even add the key into the output
                if k in out.keys():
                    out.pop(k)
                continue
            
            out[k] = vout

    elif isinstance(obj, bson.ObjectId):
        # out = {'ObjectId':str(obj)}
        out = str(obj)
    elif isinstance(obj, (str, unicode)):
        out = obj
        # This is an unlikely case, which is not handled up at the top,
        #    but could happen if the field is a list of uri's
        if kwargs.get('apply_url_prefix'):
            out = "%s%s" % (ASSET_URL, obj)
        
    elif isinstance(obj, (datetime)):
        out = str(obj)
    elif isinstance(obj, Number):
        out = obj
    elif isinstance(obj, bson.DBRef):
        if recursive:
            # We have to do a bit of lazy-loading here because the 
            # Mixin needs to know about the model class to load
            # which we could not have told it about before, due to circular
            # references
            # We can do this every time because:
            #   "When Python imports a module, it first checks the module 
            #    registry (sys.modules) to see if the module is already imported"
            model = lazy_load_model_classes(app, obj.collection, kwargs.get('model_map'))
            Context = globals().get(model)
            
            if not Context:
                app.logger.error("Missing definition in model_map (%s)" % str(kwargs.get('model_map')),
                                 "Missing Context (or import) for '%s'" % obj.collection)
                out = str(obj)
            else:
                try:
                    filters = {'id': obj.id}
                    
                    if kwargs.get('deep_filter'):
                        if obj.collection == kwargs.get('deep_filter').keys()[0]:
                            filters.update(kwargs.get('deep_filter').values()[0])
                            
                    query_function = 'objects'
                    if kwargs.get('query_function'):
                        query_function = kwargs.get('query_function').keys()[0]
                        filters.update(kwargs.get('query_function'))
                        
                        doc = getattr(Context, query_function)(**filters).first()
                        
                    else:
                        # Only apply the deref_* filters if requested
                        if kwargs.get('use_derefs'):
                            if hasattr(Context, 'deref_only_fields'):
                                doc = Context.objects(**filters).only(*Context.deref_only_fields).first()
                            elif hasattr(Context, 'deref_exclude_fields'):
                                doc = Context.objects(**filters).exclude(*Context.deref_exclude_fields).first()
                            else:
                                doc = Context.objects(**filters).first()
                        else:
                            doc = Context.objects(**filters).first()
                        
                    if not doc:
                        app.logger.error("Orphaned document: %s.id=%s" % (obj.collection, obj.id))
                        # Since this is an orphaned record, meaning it can't be decoded,
                        # don't send back a representation of it after logging
                        out = None
                    else:
                        if ( kwargs.get('types_as_str_repr') and 
                             doc._class_name in kwargs.get('types_as_str_repr') ):
                            doc = str(doc)
                        else:
                            if kwargs.get('current_depth') == depth:
                                if doc: doc = doc._data
                        
                        out = object_to_dict(obj=doc, recursive=recursive, depth=depth, **kwargs)
                except Exception as exc:
                    app.logger.error('Vars: context=%s, id=%s, depth=%s' % 
                                     (str(obj.collection), str(obj.id), depth),
                                     exc_info=True)
                    out = str(obj)
                
        else:
            out = {'collection': obj.collection, 'id': str(obj.id)}

    else:
        app.logger.debug("Could not JSON-encode type '%s': %s" % 
                         (type(obj), str(obj)))
        out = str(obj)
    
    return out

def lazy_load_model_classes(app, collection, model_map=None):
    """Lazily load modules as necessary"""
    # Ref: http://stackoverflow.com/questions/3372361/dynamic-loading-of-modules-then-using-from-x-import-on-loaded-module
    classname = ''.join([ x.capitalize() for x in collection.split('_') ])
    
    # No need to load if it's already present
    if classname in globals().keys():
        return classname
    
    appname = app.name
    appname = re.sub("\.app", "", appname)
    model_path = u"%s.%s.models" % (appname, collection)
    # import all release models into (global) namespace
    try:
        exec("from %s import %s" % (model_path, classname)) in globals()
    except ImportError as exc:
        try:
            model_path = u"%s.modules.%s.models" % (appname, collection)
            exec("from %s import %s" % (model_path, classname)) in globals()
        except ImportError as exc:
            if model_map and model_map.get(classname):
                try:
                    # Assume that the model_map provides the full path to the package
                    model_path = u"%s.%s" % (appname, model_map.get(classname))
                    exec("from %s import %s" % (model_path, classname)) in globals()
                except ImportError as exc:
                    try:
                        # It may be that the model is defined in a 'models' file under the path
                        model_path = u"%s.%s.models" % (appname, model_map.get(classname))
                        exec("from %s import %s" % (model_path, classname)) in globals()
                    except ImportError as exc:
                        try:
                            # It may be that the model is defined in a 'models' file under the path
                            model_path = u"%s.modules.%s" % (appname, model_map.get(classname))
                            exec("from %s import %s" % (model_path, classname)) in globals()
                        except ImportError as exc:
                            # It may be that the model is defined in a 'models' file under the path
                            model_path = u"%s.modules.%s.models" % (appname, model_map.get(classname))
                            exec("from %s import %s" % (model_path, classname)) in globals()
                        except Exception as exc:
                            app.logger.error("Exception lazy loading %s" % collection, exc_info=True)
                except Exception as exc:
                    app.logger.error("Exception lazy loading %s" % collection, exc_info=True)

        except Exception as exc:
            app.logger.error("Exception lazy loading %s" % collection, exc_info=True)

    except Exception as exc:
        app.logger.error("Exception lazy loading %s" % collection, exc_info=True)

    if classname not in globals().keys():
        app.logger.error("Model error: possibly model_map={'ClassName':'class.path'}! "
                         "Missing Context (or import) for '%s' => '%s'."
                         "%s vs %s" % (collection, classname, globals().keys(), classname),
                         exc_info=True)

    return classname 
