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
    '''Wrapper class to encapsulate definitions, properties, and constructs'''
    def __init__(self, definition):
        self.definitions = loadDefinitions(definition)
        self.props = getZProperties(self.definitions)
        self.constructs = getConstructs(self.definitions)

    def rebuild(self):
        '''rewrite zenpack files'''
        for c in self.constructs: c.buildZenPackFiles()

class ZenPackConstruct(ZenPackBase):
    """ Zenpack install
    """
    definitions = []
    constructs = []
    packZProperties = []

    def shouldSave(self):
        ''''''
        for d in self.definitions:
            if d.saveOld is True:  return True
        return False

    def shouldLoad(self):
        ''''''
        for d in self.definitions:
            if d.saveOld is True:  return True
        return False

    def convertToDict(self, props): return convertToDict(props)

    def saveComponents(self, app):
        ''' save components to file '''
        for c in self.constructs: saveDefinitionComponents(app, c.componentClass)

    def loadComponents(self, app):
        ''' load components from file '''
        # log.info("loading components")
        for c in self.constructs: loadDefinitionComponents(app, c.componentClass, c.addMethodName)

    def updateRelations(self, app, components=False):
        ''' update relations '''
        log.info("updating relations")
        for d in self.definitions:
            log.info("checking for relations on %s" % d.component)
            if hasattr(d, 'relmgr') and d.relmgr is not None:
                if len(d.relmgr.relations) > 1:
                    log.info("will need to update component relations for %s" % d.component)
                    components = True
        return updateRelations(app, components)

    def install(self, app):
        for c in self.constructs: c.buildZenPackFiles()
        ZenPackBase.install(self, app)
        self.updateRelations(app)
        if self.shouldLoad() is True:
            log.info("loading components")
            try: self.loadComponents(app)
            except:  log.warn("problem loading components")
        else: log.info("not loading components")

    def remove(self, app, leaveObjects=False):
        ''''''
        if self.shouldSave() is True:
            log.info("saving components")
            try: self.saveComponents(app)
            except:  log.warn("problem saving components")
        else:  log.info("not saving components")
        ZenPackBase.remove(self, app, leaveObjects)
        removeAllComponents(app, self.definitions)
        d = self.definitions[0]
        zenpackname = "%s.%s" % (d.zenpackroot, d.zenpackbase)
        removeRels(app, zenpackname)
        removeRelations(self.definitions)
        self.updateRelations(app)


