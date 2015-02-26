import logging
log = logging.getLogger('zen.zenhub')

import new
from zope.interface import classImplements
from Products.Zuul.facades import ZuulFacade
from Products.Zuul.infos.component import ComponentInfo
from Products.Zuul.infos.template import RRDDataSourceInfo
from Products.ZenUtils.Ext import DirectRouter, DirectResponse
from ZenPacks.community.ConstructionKit.CustomComponent import *
from ZenPacks.community.ConstructionKit.CustomDataSource import *
from ZenPacks.community.ConstructionKit.Template import *
from zope.schema.vocabulary import SimpleVocabulary
from Products.Zuul.decorators import info

def stringToMethod(methodName,methodString):
    """
        return a python method given string representing the method
    """
    data = {}
    exec methodString in data
    return data[methodName]

class ClassHelper(object):
    """
    Standardize the layout of associate classes
    """
    classname = ''
    compname = 'os'
    infoname = ''
    interfacename = ''
    indent = 4*' '
    classes = []
    template = Template()
    
    def __init__(self, classname, compname, base, root):
        ''' set default vars'''
        self.zenpackbase = base
        self.zenpackroot = root
        self.zenpackname = "%s.%s" % (root, base)
        self.classes = []
        self.classname = classname
        self.compname = compname
        self.infoname = "%sInfo" % self.classname
        self.interfacename = "I%s" % self.infoname
        self.facadename = "%sFacade" % self.zenpackbase
        self.ifacadename = "I%s" % self.facadename
        self.adaptername = "%sAdapter" % self.zenpackbase
        self.routername = "%sRouter" % self.zenpackbase
    
    def addClassData(self, name, path, klass):
        ''' add class to helper'''
        self.classes.append({ 'name': name, 'path': path, 'class' : klass })
        setattr(ClassHelper, name, klass)
    
    def componentClass(self, parents, data):
        '''build component class'''
        # basic class object
        self.classobject = type(self.classname, tuple(parents), data)
        # add properties from inherited parent classes
        for p in parents:
            try:
                currents = [x[0] for x in self.classobject._relations] + [self.compname]
                diffs = [x for x in p._relations if x[0] not in (currents)]
                self.classobject._relations += tuple(diffs)
            except:  pass
        # set attributes for class
        for k,v in data.items():  setattr(self.classobject,k,v)
        # set module path
        self.class_path = "%s.%s" % (self.zenpackname, self.classname)
        # export finalized class object
        self.addClassData(self.classname, self.class_path, self.classobject)
        
    def datasourceClass(self, data):
        '''build datasource class'''
        # basic class
        self.classobject = type(self.classname, (CustomDataSource,), data)
        # set module path
        self.class_path = "%s.datasources.%s" % (self.zenpackname, self.classname)
        # export finalized class object
        self.addClassData(self.classname, self.class_path, self.classobject)
    
    def interfaceClass(self,data, ds=False):
        '''build interfaces class'''
        if ds == True:  klasstext = self.template.DATASOURCE_INTERFACE % self.interfacename
        else:  klasstext = self.template.COMPONENT_INTERFACE % self.interfacename
        self.interfaceclass = self.stringToPython(self.interfacename, klasstext)
        self.interfaceclass._InterfaceClass__attrs.update(data)
        self.interface_path = "%s.interfaces.%s" % (self.zenpackname, self.interfacename)
        self.addClassData(self.interfacename, self.interface_path, self.interfaceclass)
    
    def ifacadeClass(self,data): 
        '''build interfaces facade'''
        klasstext = self.template.FACADE_CLASS % (self.ifacadename,self.indent)
        self.ifacadeclass = self.stringToPython(self.ifacadename, klasstext)
        self.ifacade_path = "%s.interfaces.%s" % (self.zenpackname, self.ifacadename)
        self.addClassData(self.ifacadename, self.ifacade_path, self.ifacadeclass)

    def facadeClass(self, data):
        '''build facades class'''
        args = {}
        args[data['name']] = self.stringToPython(data['name'], data['text'])
        self.facadeclass = type(self.facadename,(ZuulFacade,), args)
        classImplements(self.facadeclass, self.ifacadeclass)
        self.facade_path = "%s.facades.%s" % (self.zenpackname, self.facadename)
        self.addClassData(self.facadename, self.facade_path, self.facadeclass)

    def infoClass(self, data, ds=False):
        '''build info class'''
        if ds == True:  self.infoclass = type(self.infoname,(RRDDataSourceInfo,),data)
        else:  self.infoclass = type(self.infoname,(ComponentInfo,),data)
        classImplements(self.infoclass,self.interfaceclass)
        self.info_path = "%s.info.%s" % (self.zenpackname, self.infoname)
        self.addClassData(self.infoname, self.info_path, self.infoclass)
    
    def routerClass(self,data):
        '''build router class'''
        getmethod = self.template.ROUTER_CLASS % (self.indent, self.indent, self.adaptername)
        args = {}
        args['_getFacade'] = self.stringToPython('_getFacade', getmethod)
        args[data['name']] = self.stringToPython(data['name'], data['text'])
        self.routerclass = type(self.routername, (DirectRouter,), args)
        self.router_path = "%s.routers.%s" % (self.zenpackname, self.routername)
        self.addClassData(self.routername, self.router_path, self.routerclass)

    def addClassInterface(self, klass, data):
        '''add properties to Zope interface objext'''
        super(type(klass), klass).__dict__['_InterfaceClass__attrs'].update(data)
        return klass
    
    def updateClassProperties(self, object, data):
        '''add properties to Zope class objext'''
        super(type(object),object).__dict__.update(data)
    
    def addClassTextMethod(self, object, methodname, methodtext):
        '''add new method to existing class'''
        #print "adding text method %s: %s" % (object.__name__, methodname)
        setattr(object, methodname, self.stringToPython(methodname, methodtext))
    
    def addClassMethod(self, object, methodname, methodobject):
        '''add new method to existing class'''
        #print "adding class method %s: %s" % (object.__name__, methodname)
        setattr(object, methodname, new.instancemethod(methodobject, None, object))
    
    def stringToPython(self, name, text):
        '''return a python object given string representing the object'''
        #self.logMethod(name, text)
        data = {}
        exec text in data
        return data[name]
    
    def logMethod(self, name, text):
        '''log given text'''
        log.debug("adding method: %s" % name)
        for line in text.split('\n'):  log.debug(line)

