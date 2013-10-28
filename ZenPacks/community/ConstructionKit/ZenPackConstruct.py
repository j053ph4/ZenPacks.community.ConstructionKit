import Globals
import logging
log = logging.getLogger('zen.zenhub')
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.Template import *
from ZenPacks.community.ConstructionKit.ZenPackHelper import *
from transaction import commit
import cPickle as pickle


class Initializer(object):
    ''''''
    def __init__(self, definition):
        self.definitions = loadDefinitions(definition)
        self.props = getZProperties(self.definitions)
        self.constructs = getConstructs(self.definitions)
        
class ZenPackConstruct(ZenPackBase):
    """ Zenpack install
    """
    definitions = []
    constructs = []
    packZProperties = []
    
    def convertToDict(self, props):
        return convertToDict(props)
    
    def saveComponents(self, app):
        ''' save components to file '''
        log.info("saving components")
        for d in self.definitions:
            saveDefinitionComponents(app, d)
    
    def loadComponents(self, app):
        ''' load components from file '''
        log.info("loading components")
        for c in self.constructs:
            loadDefinitionComponents(app, c.componentClass, c.addMethodName)
    
    def updateRelations(self, app, components=False):
        ''' update relations '''
        log.info("updating relations")
        for d in self.definitions:
            try:
                if len(d.relmgr.relations) > 1:
                    components=True
            except:
                pass
        return updateRelations(app,components)
    
    def install(self, app):
        for c in self.constructs:
            c.buildZenPackFiles()
        ZenPackBase.install(self, app)
        self.updateRelations(app)
        #self.loadComponents(app)
    
    def remove(self, app, leaveObjects=False):
        #self.saveComponents(app)
        removeAllComponents(app, self.definitions)
        ZenPackBase.remove(self, app, leaveObjects)
        d = self.definitions[0]
        zenpackname = "%s.%s" % (d.zenpackroot, d.zenpackbase)
        removeRels(app, zenpackname)
        removeRelations(self.definitions)
        self.updateRelations(app)

