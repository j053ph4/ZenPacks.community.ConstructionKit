import logging
log = logging.getLogger('zen.zenhub')
from Products.ZenRelations.RelSchema import *
from ZenPacks.community.ConstructionKit.ClassHelper import stringToMethod
import importlib

class CustomRelations(object):
    '''
    Class to handle custom object relations
    '''
    def __init__(self):
        self.relations = []
        self.fromrelations =  []
        self.torelations = []
    
    def fixClass(self,name):
        for r in self.relations:
            r['fromClass'] = name
            
    def add(self, fromName, fromType, fromClass, toName, toType, toClass, createTo=True, createFrom=True):
        info = {
                'fromName' : fromName,
                'toName' : toName,
                'fromType' : fromType,
                'toType' : toType,
                'toClass' : toClass,
                'fromClass' : fromClass,
                'createTo' : createTo,
                'createFrom' : createFrom
                }
        if info not in self.relations:  self.relations.append(info)
    
    def createFrom(self, info):
        if info['createFrom'] == True:
            relation = ("%s" % info['toName'], info['toType'](info['fromType'], "%s" % info['toClass'], "%s" % info['fromName']))
            return relation
        return None
    
    def createTo(self, info):
        if info['createTo'] == True:
            relation = ("%s" % info['fromName'], info['fromType'](info['toType'], "%s" % info['fromClass'], "%s" % info['toName']))
            target = self.import_class(info['toClass'])
            return (target, relation)
        return None
    
    def createFromRelations(self):
        for r in self.relations:
            rel = self.createFrom(r)
            if rel is not None:  
                if rel not in self.fromrelations:  self.fromrelations.append(rel)

    def createToRelations(self):
        for r in self.relations:
            rel = self.createTo(r)
            if rel is not None:  
                if rel not in self.torelations:  self.torelations.append(rel)
    
    def addToRelations(self):
        for target, relation in self.torelations:
            relname, schema = relation
            add = True
            for x in target._relations:
                if x[0] == relname:
                    add = False
            if add is True:
                target._relations += (relation,)
       
    def removeToRelations(self):
        for target, relation in self.torelations:
            relname, schema = relation
            log.info("removing TO rel %s from %s to %s" % (relname, target.__name__, schema.remoteClass))
            target._relations = tuple([x for x in target._relations if x[0] not in (relname)])
    
    def addFromRelations(self):
        for relation in self.fromrelations:
            relname, schema = relation
            target = self.loadSchemaTarget(schema)
            add = True
            for x in target._relations:
                if x[0] == relname:
                    add = False
            if add is True:
                target._relations += (relation,)
        return tuple(self.fromrelations)
    
    def removeFromRelations(self):
        for relname, schema in self.fromrelations:
            target = self.loadSchemaTarget(schema)
            log.info("removing FROM rel %s from %s to %s" % (relname, target.__name__, schema.remoteClass))
            target._relations = tuple([x for x in target._relations if x[0] not in (relname)])
            
    def loadSchemaTarget(self, schema):
        ''' load all Definition classes from python module'''
        import inspect, importlib
        module = importlib.import_module(schema.remoteClass) 
        members = inspect.getmembers(module, inspect.isclass)
        for m,n in members:
            try:
                if n.__module__ == module.__name__:
                    return n
            except:
                pass
        return None

    def import_class(self, name):
        '''find and return target class object'''
        m = importlib.import_module(name)
        classname = name.split('.')[-1]
        return getattr(m, classname)
