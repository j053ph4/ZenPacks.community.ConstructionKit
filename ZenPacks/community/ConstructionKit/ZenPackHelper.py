import Globals
import logging
log = logging.getLogger('zen.zenhub')
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.Template import *
from transaction import commit
import cPickle as pickle


def removeInstanceRelations(app, classname, relname):
    '''remove all instances of a relation on a class'''
    brains = app.getDmd().global_catalog(meta_type=classname)
    for b in brains:
        ob = b.getObject()
        ob._delObject(relname)

def countConstructs(app):
    '''return  the number of each type of custom components'''
    import importlib
    packs = findDefinitionPacks(app)
    cat = app.getDmd().global_catalog
    for p in packs:
        if p.id == 'ZenPacks.community.ConstructionKit':  continue
        modname = "%s.Definition" % p.moduleName()
        module = importlib.import_module(modname)
        defs = loadDefinitions(module)
        for d in defs:  print "%s: %s" % (d.component,len(cat(meta_type=d.component)))

def exportDevelopmentPacks(app):
    '''export all zenpacks currently in development mode'''
    for p in app.ZenPackManager.packs():
        if p.isDevelopment() is True:  p.manage_exportPack()
            
def exportDefinitionPacks(app):
    '''export Definition-related zenpacks'''
    packs = findDefinitionPacks(app)
    for p in packs:  p.manage_exportPack()

def findZenPack(name):
    ''' find a particular zenpack '''
    for p in app.ZenPackManager.packs():
        if p.id == name:  return p
    return None

def findDefinition(zenpack):
    ''' find a zenpack's definition file '''
    for f in zenpack.getFilenames():
        if 'Definition' in f:  return f
    return None

def findDefinitionPacks(app):
    ''' find zenpacks with definition files '''
    packs = []
    for p in app.ZenPackManager.packs():
        # skip the ConstructionKit itself
        if p.id == 'ZenPacks.community.ConstructionKit': continue
        for f in p.getFilenames():
            if 'Definition' in f:  packs.append(p)
    return packs

def findDefinitionFiles(app):
    ''' get list of definition files '''
    definitions = []
    for p in app.ZenPackManager.packs():
        # skip the ConstructionKit itself
        if p.id == 'ZenPacks.community.ConstructionKit': continue
        file = findDefinition(p)
        if file is not None:  definitions.append(file)
    return definitions

def loadDefinitions(module):
    ''' load all Definition classes from python module'''
    import inspect
    defs = []
    members = inspect.getmembers(module, inspect.isclass)
    for m,n in members:
        try:
            if n.__module__ == module.__name__:  defs.append(n)
        except: 
            log.warn("couldn't append %s to defs" % n)
    return defs

def migrateDefinitions(app):
    ''' rewrite old definition files (pre-2.0)'''
    import imp,re, pprint, importlib
    template = Template()
    packs = findDefinitionPacks(app)
    ignoreKeys = ['cwd','provided', 'cycletime', 'timeout', 'useCommand']
    for p in packs:
        modname = "%s.Definition" % p.moduleName()
        try:
            module = importlib.import_module(modname)
            defs = loadDefinitions(module)
            for d in defs:
                data = {}
                dname = "%sDefinition" % d.component
                for k,v in d.__dict__.items():
                    if '__' in k: continue
                    if k in ignoreKeys:  continue
                    if k == 'parentClass': data[k] = [v]
                    else: data[k] = v
                printedData = pprint.pformat(data).replace('\n','\n     ')
                output = template.DEFINITION_SUBCLASS % (printedData, dname, dname)
                file = "%s.Definition2.py" % p.path()
                newfile = open(file,'w')
                newfile.write(output)
        except:  log.warn("couldn't migrate defitions file for %s" % p)

def getConstructs(definitions):
    ''' create all constructs for a set of definitions '''
    from ZenPacks.community.ConstructionKit.Construct import Construct
    constructs = []
    for d in definitions:
        c = Construct(d)
        constructs.append(c)
    addRelations(definitions)
    return constructs

def addRelations(definitions):
    '''
        add the other side of custom relations after classes are all built
    '''
    from ZenPacks.community.ConstructionKit.Construct import Construct
    c = Construct()
    for d in definitions:
        packname = "%s.%s" % (d.zenpackroot, d.zenpackbase)
        construct = c.packs[packname]['constructs'][d.__name__]['component']
        construct.relmgr.createToRelations()
        construct.relmgr.addToRelations()
        
def removeRelations(definitions):
    '''
        add the other side of custom relations after classes are all built
    '''
    from ZenPacks.community.ConstructionKit.Construct import Construct
    c = Construct()
    constructs = []
    for d in definitions:
        packname = "%s.%s" % (d.zenpackroot, d.zenpackbase)
        construct = c.packs[packname]['constructs'][d.__name__]['component']
        constructs.append(construct)
    for c in constructs: c.relmgr.removeFromRelations()
    for c in constructs: c.relmgr.removeToRelations()

def removeRelObjects(app, classname, relname):
    '''delete all class-based objects directly from catalog'''
    log.info("removing %s from %s objects" % (relname, classname))
    brains = app.getDmd().global_catalog(meta_type=classname)
    for b in brains:
        ob = b.getObject()
        try: ob._delObject(relname)
        except: 
            try: updateRelation(ob)
            except: log.warn("problem with %s" % ob.id)
    commit()

def removeRels(app, zenpack):
    '''remove relations from zenpack-based objects'''
    from ZenPacks.community.ConstructionKit.Construct import Construct
    c = Construct()
    constructs = c.packs[zenpack]['constructs']
    for d in constructs.keys():
        component = constructs[d]['component']
        for rel in component.relmgr.relations:
            classname = rel['toClass'].split('.')[-1]
            relname = rel['fromName']
            removeRelObjects(app, classname, relname)
         
def getZProperties(definitions):
    ''' retrive a list of zProperties to be added '''
    props = []
    for d in definitions:
        for p in d.packZProperties:
            if p not in props: props.append(p)
    return props

def updateRelations(app, component=False):
    ''' update device relations '''
    dmd = app.getDmd()
    log.info("updating relations")
    log.info('  Services')
    for b in dmd.Services.serviceSearch(): updateRelation(b.getObject())
    log.info("  Groups")
    for ob in dmd.Groups.getSubOrganizers():  updateRelation(ob)
    log.info("  Systems")
    for ob in dmd.Systems.getSubOrganizers():  updateRelation(ob)
    log.info("  Locations")
    for ob in dmd.Locations.getSubOrganizers():  updateRelation(ob)
    log.info("  Networks")
    for net in dmd.Networks.getSubNetworks():
        updateRelation(net)
        for ob in net.ipaddresses(): updateRelation(ob)
    log.info("  IPv6Networks")
    for net in dmd.IPv6Networks.getSubNetworks():
        updateRelation(net)
        for ob in net.ipaddresses(): updateRelation(ob)
    log.info('  Processes')
    for p in dmd.Processes.getSubOSProcessClassesGen():  updateRelation(p)
    commit()
    log.info("  Devices")
    for dev in dmd.Devices.getSubDevices():
        updateRelation(dev)
        updateRelation(dev.os)
        updateRelation(dev.hw)
        if component == True:
            for c in dev.getDeviceComponents():
                updateRelation(c)
        commit()
        
def updateRelation(ob):
    '''try to make relations current'''
    # first try straight build
    try:  ob.buildRelations()
    except: 
        # next try check/repair
        try: ob.checkRelations(repair=True)
        except:
            try:
                # more drastic fix
                for name, schema in ob._relations:
                    try: ob._setObject(name, schema.createRelation(name))
                    except:  pass
            except:
                try:
                    # even more drastic, delete and recreate all relations
                    for name, schema in ob._relations:
                        try: 
                            delattr(ob,name)
                            ob._setObject(name, schema.createRelation(name))
                        except:  pass
                except:
                    log.warn("error updating relations for %s" % ob.id)

def getDefinitionComponents(app, classname):
    '''return all component instances of a given class'''
    log.info("getting all %s components" % classname)
    components = []
    brains = app.dmd.global_catalog(meta_type=classname)
    for b in brains: components.append(b.getObject())
    log.info("found %s %s components" % (len(components), classname))
    return components

def removeAllComponents(app, definitions):
    ''' remove all construct-related components '''
    for d in definitions: removeDefinitionComponents(app, d)

def removeDefinitionComponents(app, definition):
    '''remove all definition-related components'''
    components = getDefinitionComponents(app, definition.component)
    log.info("removing %s %s components" % (len(components), definition.component))
    for c in components:
        try: c.manage_deleteComponent()
        except:
            try: c.getPrimaryParent()._delObject(c.id)
            except: log.warn("ERROR REMOVING %s: %s on %s" % (name,c.id,  definition.component))
    try: commit()
    except:
        log.warn("conflict detected, reattempting for %s" %  definition.component)
        sync()
        removeDefinitionComponents(app, definition)

def saveDefinitionComponents(app, classname):
    ''' save components to file '''
    components = getDefinitionComponents(app, classname)
    dataFile = '/tmp/%s.p' % classname
    data = {}
    for c in components:
        try:
            props = []
            for k,v in c.propertyItems():
                if hasattr(v, '__call__'): continue
                props.append((k,v))
            data[c.device().id] = {classname: {c.id: props}}
            log.info("saving %s from %s" % (c.id, c.device().id))
        except: log.warn("had trouble saving data for %s from %s" % (c.id, c.device().id))
    import cPickle as pickle
    with open(dataFile, 'wb') as fp: pickle.dump(data, fp)

def loadDefinitionComponents(app, classname, addmethod):
    ''' load components from file '''
    dataFile = '/tmp/%s.p' % classname
    data = {}
    try:
        with open(dataFile, 'rb') as fp: data = pickle.load(fp)
        for dev in data.keys():
            device = app.dmd.Devices.findDevice(dev)
            compdict = data[dev]
            compitems = compdict[classname].keys()
            for i in compitems:
                item = compdict[classname][i]
                props = convertToDict(item)
                method = getattr(device, addmethod)
                try:
                    c = method(**props)
                    log.info("added %s to %s" % (c.id,device.id))
                except:
                    log.warn("problem adding %s to %s" % (c.id,device.id))
            commit()
    except: pass
        
def convertToDict(props):
    ''' convert list of properties to dict'''
    output = {}
    for p in props:
        k,v = p
        try: output[k] = v
        except: pass
    return output


