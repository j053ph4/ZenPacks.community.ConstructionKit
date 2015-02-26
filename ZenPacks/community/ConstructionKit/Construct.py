import logging
log = logging.getLogger('zen.zenhub')
import os, inspect
from ZenPacks.community.ConstructionKit.CustomProperty import *
from ZenPacks.community.ConstructionKit.ZenPackBuilder import *
from ZenPacks.community.ConstructionKit.Prototype import *
from ZenPacks.community.ConstructionKit.BasicDefinition import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
from ZenPacks.community.ConstructionKit.Template import *
from ZenPacks.community.ConstructionKit.CustomRelations import *

class Construct(object):
    '''hold info about all the constructed packs, definitions, constructs, properties, etc'''
    zenpackroot = None
    zenpackbase = None
    zenpackname = None
    componentClass = None
    datasourceClass = None
    compname = 'os'
    packs = {}
    indent = 4*' '
    template = Template()
    collector_text = template.ON_COLLECTOR_INSTALLED
    
    def __init__(self,d=None):
        ''''''''
        if d is not None:  self.addDefinition(d)
    
    def addDefinition(self, d):
        ''' initialize definition objects'''
        self.definition = d.__name__
        self.cwd = os.path.dirname(inspect.getabsfile(d))
        #print "PRE: %s has %s methods" % (d.component, len(d.componentMethods))
        d = update(d)
        self.d = d
        #print "POST: %s has %s methods" % (self.d.component, len(self.d.componentMethods))
        log.debug("reading %s" % self.definition)
        self.compdata = self.fixPropertyId(self.d.componentData['properties'])
        self.dsdata = self.fixPropertyId(self.d.datasourceData['properties'])
        self.zenpackroot = self.d.zenpackroot
        self.zenpackbase = self.d.zenpackbase
        self.zenpackname = "%s.%s" % (self.zenpackroot, self.zenpackbase)
        self.componentClass = self.d.component
        self.compname = self.d.compname
        self.singular = self.d.componentData['singular']
        self.plural = self.d.componentData['plural']
        self.manual = self.d.addManual
        self.datasourceClass = '%sDataSource' % d.component
        if self.zenpackname not in self.packs.keys():
            log.debug("adding %s to packs" % self.zenpackname)
            self.packs[self.zenpackname] = {'constructs' : {},
                                            'builder' : ZenPackBuilder(self.cwd, self.zenpackname, self.indent),
                                            'properties' : {},
                                            'zenpack': None,
                                            }
        self.packs[self.zenpackname]['constructs'][self.definition] = {'component': None, 'datasource': None}
        self.packs[self.zenpackname]['properties'][self.definition] = {'component': self.compdata, 'datasource': self.dsdata }
        self.packs[self.zenpackname]['builder'].addHelper(self.d.component, self.definition)
        self.buildComponent()
        if self.d.createDS == True:  self.buildDataSource()
    
    def buildComponent(self):
        '''build component class objects'''
        #log.debug("%s Building Component: %s %s" % (8*'#', self.d.component,8*'#'))
        construct = Prototype(self.zenpackroot, self.zenpackbase, self.compname, self.indent)
        construct.addComponent(self.d.component, self.singular, self.plural, self.manual, self.compdata)
        construct.relmgr =  self.d.relmgr
        construct.relmgr.createFromRelations()
        # add data for parent classes (if any)
        for p in self.d.parentClasses:  
            construct.classdata['parents'].append(p)
            construct.classdata['_properties'] += p._properties
        # update more component class attributes
        construct.classdata['class'].update({'nameKey': self.d.componentData['displayed'],
                                             'primaryKey' : self.d.componentData['primaryKey'],
                                             'portal_type' : self.d.component,
                                             'meta_type' : self.d.component,
                                             })
        # start a new helper to build the class
        construct.getHelper()
        # add any custom methods
        #print "adding %s methods to %s" % (len(self.d.componentMethods), construct.helper.classobject.__name__)
        for m in self.d.componentMethods:  setattr(construct.helper.classobject, m.__name__, m)
        # set any default attributes
        for k,v in self.d.componentAttributes.items():  setattr(construct.helper.classobject, k, v)
        # backwards compatibility
        self.setBackwardsCompatVars(construct)
        # make sure construct is added to local packs data
        if self.packs[self.zenpackname]['zenpack'] is None:  self.packs[self.zenpackname]['zenpack'] = construct
        self.packs[self.zenpackname]['constructs'][self.definition]['component'] = construct
        self.packs[self.zenpackname]['builder'].helpers[self.d.component]['component'] = construct
        self.updateZenPackClasses(construct)
    
    def buildDataSource(self):
        '''build datasource class objects'''
        #log.debug("%s Building DataSource: %s %s" % (8*'#',self.datasourceClass,8*'#'))
        construct = Prototype(self.zenpackroot, self.zenpackbase, self.indent)
        construct.addDataSource(self.datasourceClass, self.dsdata)
        construct.is_datasource = True
        construct.classdata['class'].update({
                                             'ZENPACKID': self.zenpackname,
                                             'DATASOURCE' : '%s'% self.d.component,
                                             'sourcetypes' : (self.d.component,),
                                             'sourcetype' : self.d.component,
                                             'component' : '${here/%s}' % self.d.componentData['displayed'],
                                             'cmdFile' : self.d.cmdFile,
                                             'dpoints' : self.d.datapoints,
                                             })
        # start a new helper to build the class
        construct.getHelper()
        # append any overridden methods
        for m in self.d.datasourceMethods:  setattr(construct.helper.classobject, m.__name__, m)
        # update any properties that should be ignored by getCommand
        for x in self.d.ignoreKeys:  construct.helper.classobject.ignoreKeys.append(x)
        # update local packs data
        self.packs[self.zenpackname]['constructs'][self.definition]['datasource'] = construct
        self.packs[self.zenpackname]['builder'].helpers[self.d.component]['datasource'] = construct
    
    def fixPropertyId(self, properties):
        ''' append id and order to properties for backwards compatibility'''
        #log.debug("fixPropertyId")
        data =[]
        # set order in Details Pane
        order = 1
        ids = properties.keys()
        ids.sort()
        for i in ids:
            p = properties[i]
            p.id  = i
            if p.order is None:
                p.order = order
                order += 1
            else: order = p.order + 1
            data.append(p)
        return data
    
    def rebuild(self):
        '''rebuild files for all Zenpacks'''
        #log.debug("rebuild")
        packs = self.packs.keys()
        for p in packs:
            print "rebuilding %s" % p
            self.zenpackname = p
            self.buildZenPackFiles()
    
    def buildZenPackFiles(self, new=True):
        ''' build zenpack-related files '''
        #log.debug("buildZenPackFiles")
        self.packs[self.zenpackname]['builder'].zenpack = self.packs[self.zenpackname]['zenpack']
        builder = self.packs[self.zenpackname]['builder']
        builder.clear_files()
        builder.build_skel()
        builder.buildFiles()
        log.debug("building %s files for %s" % ( len(builder.files), self.zenpackname))
        for f in builder.files:
            print 'writing %s' % f['name']
            log.debug('writing %s' % f['name'])
            builder.writeLines(f['name'],f['text'])
    
    def updateZenPackClasses(self, c):
        '''
            add combined methods to facades, ifacades, and routers
        '''
        #log.debug("updateZenPackClasses")
        construct = self.packs[self.zenpackname]['zenpack']
        helper = construct.helper
        helper.addClassMethod(
                              helper.facadeclass, 
                              c.methods['facade']['name'],
                              helper.stringToPython(c.methods['facade']['name'], c.methods['facade']['text'])
                              )
        method = helper.stringToPython(c.methods['ifacade']['name'], c.methods['ifacade']['text'])
        helper.addClassMethod(
                              helper.ifacadeclass,
                              c.methods['ifacade']['name'],
                              method,
                              )
        helper.ifacadeclass._InterfaceClass__attrs.update({c.methods['ifacade']['name']: method})
        helper.addClassMethod(
                              helper.routerclass,
                              c.methods['router']['name'],
                              helper.stringToPython(c.methods['router']['name'], c.methods['router']['text'])
                              )
        
        method = helper.stringToPython(c.methods['ifacade']['name'], c.methods['ifacade']['text'])
        helper.addClassMethod(
                              helper.ifacadeclass,
                              c.methods['ifacade']['name'],
                              method,
                              )
        self.packs[self.zenpackname]['builder'].zenpack = construct
    
    def setBackwardsCompatVars(self, construct):
        ''' vars provided for backwards compat'''
        #log.debug("setBackwardsCompatVars")
        self.addMethodName = construct.methods['add']['name']
        self.addMethod = construct.methods['add']['text']
        self.relname = construct.relname
        self.zenpackComponentModule = "%s.%s" % (construct.zenpackname, construct.classname)
        self.baseid = construct.baseid
        self.deviceToComponent = ((construct.relname, ToManyCont(ToOne, self.zenpackComponentModule, construct.compname)),)
    
    def onCollectorInstalled(self):
        '''returns error if command file not present on collector'''
        if self.d.cmdFile: return self.collector_text % (self.d.component, self.d.component, self.d.cmdFile)
        else: return '''def onCollectorInstalled(ob, event):\n    pass'''
    
    def addDeviceRelation(self): pass

