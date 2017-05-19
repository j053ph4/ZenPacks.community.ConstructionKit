from Products.ZenModel.migrate.Migrate import Version
from ZenPacks.community.ConstructionKit.CustomProperty import *
from ZenPacks.community.ConstructionKit.CustomRelations import *
# from ZenPacks.community.ConstructionKit.CustomComponent import getFixedPasswords,setFixedPasswords
import logging
log = logging.getLogger('zen.zenhub')

def fixDict(old, new):
    for a, b in new.items():
        if type(b) == dict:
            try:  old.update(fixDict(old[a], new[a]))
            except:  old[a] = b
        else:
            try:  test = old[a]
            except:  old[a] = b
    return old

def update(ob):
    '''
        update Definition with BasicDefinition properties
    '''
    base = BasicDefinition()
    base.reset()
    basedata = base.__dict__.copy()
    newdata = ob.__dict__.copy()
    updateddata = fixDict(newdata, basedata)
    object = ob()
    for k, v in updateddata.items():  setattr(object, k , v)
    object.component = ob.component
    object.datasourceData['properties'].update(object.componentData['properties'].copy())
    object.fromClass = "%s.%s.%s" % (object.zenpackroot, object.zenpackbase, object.component)
    relname = "%s%ss" % (ob.component.lower()[:1], ob.component[1:])
    if object.compname == "hw": object.relmgr.add(relname, ToManyCont, object.fromClass, 'hw', ToOne, 'Products.ZenModel.DeviceHW')
    else: object.relmgr.add(relname, ToManyCont, object.fromClass, 'os', ToOne, 'Products.ZenModel.OperatingSystem')
    return object

def addDefinitionDeviceRelation(definition,
                              fromname, fromtype, fromclass, fromattribute,
                              toname, totype, toclass, toattribute,
                              title=None, linkattrib=None):
    ''' link from component to another device '''
    if title == None: title = toname.capitalize()
    if linkattrib == None: linkattrib = fromattribute
    data = {
            'get': {
                    'name': "get%s" % toname.capitalize(),
                    'text': '''def %s(ob):  return ob.findDevice(ob.%s, '%s')\n''',
                    'args': (fromattribute, toattribute),
                    },
            'set': {
                    'name': "set%s" % toname.capitalize(),
                    'text': '''def %s(ob, name=''): ob.setCustomRelation(ob.findDevice(ob.%s, '%s'), '%s', '%s')\n''',
                    'args': (fromattribute, toattribute, toname, fromname)
                    },
            'link': {
                    'name': "get%sLink" % toname.capitalize(),
                    'text': '''def %s(ob):  return ob.getRelatedDeviceLink("%s", ob.%s)\n''',
                    'args': (toname, linkattrib)
                    },
            }
    addRelations(definition, title, data, fromname, fromtype, fromclass, toname, totype, toclass)


def addDefinitionSelfComponentRelation(definition,
                              fromname, fromtype, fromclass, fromattribute,
                              toname, totype, toclass, toattribute, title=None, linkattrib=None):
    ''' link from component to another component on the same device '''
    # log.debug("addDefinitionSelfComponentRelation FROM: %s-%s TO: %s-%s" % (fromname,fromclass,toname,toclass))
    if title == None: title = toname.capitalize()
    if linkattrib == None: linkattrib = toattribute
    classname = toclass.split('.')[-1]
    data = {
            'get': {
                    'name': "get%s" % toname.capitalize(),
                    'text': '''def %s(ob):  return ob.findDeviceComponent(ob.device(), '%s', '%s', ob.%s)\n''',
                    'args': (classname, toattribute, fromattribute),
                    },
            'set': {
                    'name': "set%s" % toname.capitalize(),
                    'text': '''def %s(ob, name=''): ob.setCustomRelation(ob.findDeviceComponent(ob.device(), '%s', '%s', ob.%s), '%s', '%s')\n''',
                    'args': (classname, toattribute, fromattribute, toname, fromname)
                    },
            'link': {
                    'name': "get%sLink" % toname.capitalize(),
                    'text': '''def %s(ob):\n    try:\n        return ob.getRelatedComponentLink('%s','%s')\n    except:\n        pass\n''',
                    'args': (toname, linkattrib)
                    },
            }
    addRelations(definition, title, data, fromname, fromtype, fromclass, toname, totype, toclass)


def addDefinitionDeviceComponentRelation(definition, devkey, devvalue,
                              fromname, fromtype, fromclass, fromattribute,
                              toname, totype, toclass, toattribute,
                               title=None, linkattrib=None):
    ''' link from component to another component on another device '''
    if title == None: title = toname.capitalize()
    if linkattrib == None: linkattrib = toattribute
    classname = toclass.split('.')[-1]
    data = {
            'get': {
                    'name': "get%s" % toname.capitalize(),
                    'text': '''def %s(ob):  return ob.findDeviceComponent(ob.findDevice(ob.%s, '%s'), '%s', '%s', ob.%s)\n''',
                    'args': (devvalue, devkey, classname, toattribute, fromattribute),
                    },
            'set': {
                    'name': "set%s" % toname.capitalize(),
                    'text': '''def %s(ob, name=''): ob.setCustomRelation(ob.findDeviceComponent(ob.findDevice(ob.%s, '%s'), '%s','%s', ob.%s ), '%s', '%s')\n''',
                    'args': (devvalue, devkey, classname, toattribute, fromattribute, toname, fromname)
                    },
            'link': {
                    'name': "get%sLink" % toname.capitalize(),
                    'text': '''def %s(ob):\n    try:\n        return ob.getRelatedComponentLink('%s','%s')\n    except:\n        pass\n''',
                    'args': (toname, linkattrib)
                    },
            }
    addRelations(definition, title, data, fromname, fromtype, fromclass, toname, totype, toclass)

def addDefinitionAnyComponentRelation(definition,
                              fromname, fromtype, fromclass, fromattribute,
                              toname, totype, toclass, toattribute,
                              title=None, linkattrib='id'):
    ''' link from component to another component on another device '''
    if title == None: title = toname.capitalize()
    classname = toclass.split('.')[-1]
    data = {
            'get': {
                    'name': "get%s" % toname.capitalize(),
                    'text': '''def %s(ob):  return ob.findComponent('%s', '%s', ob.%s)\n''',
                    'args': (classname, toattribute, fromattribute),
                    },
            'set': {
                    'name': "set%s" % toname.capitalize(),
                    'text': '''def %s(ob, name=''): ob.setCustomRelation(ob.findComponent('%s','%s', ob.%s ), '%s', '%s')\n''',
                    'args': (classname, toattribute, fromattribute, toname, fromname)
                    },
            'link': {
                    'name': "get%sLink" % toname.capitalize(),
                    'text': '''def %s(ob):\n    try:\n        return ob.getRelatedComponentLink('%s','%s')\n    except:\n        pass\n''',
                    'args': (toname, toattribute)
                    },
            }
    addRelations(definition, title, data, fromname, fromtype, fromclass, toname, totype, toclass)

def addRelations(definition, title, data, fromname, fromtype, fromclass, toname, totype, toclass):
    '''add methods and relations to component definition'''
    addMethods(definition, title, data)
    if definition.relmgr is None:  definition.relmgr = CustomRelations()
    definition.relmgr.add(fromname, fromtype, fromclass, toname, totype, toclass)
    definition.relmgr.info()

def addMethods(definition, title, data={}):
    ''' add get, set, and link methods to a supplemental relation'''
    from ZenPacks.community.ConstructionKit.ClassHelper import stringToMethod
    methods = []
    names = []
    for v in data.values():
        name = v['name']
        args = (name,)
        args += v['args']
        text = v['text'] % args
        names.append(name)
        methods.append(stringToMethod(v['name'], text))
    definition.componentMethods += methods
    definition.componentData['properties'][ data['set']['name'].lower() ] = getSetter(data['set']['name'])
    definition.componentData['properties'][ data['link']['name']] = getReferredMethod(title, data['link']['name'])
    definition.ignoreKeys += names
    definition.ignoreKeys += [data['set']['name'].lower(), data['link']['name']]


def getBasicDefinitionData(version, root, base, component, singular, plural):
    '''basic Definition dictionary'''
    return {
        'version' : version,
        'zenpackroot' : root,
        'zenpackbase': base,
        'packZProperties' : [],
        'componentMethods' : [],
        'componentAttributes' : {},
        'parentClasses': [],
        'relmgr' : CustomRelations(),
        'addManual': False,
        'component' : component,
        'compname' : 'os',
        'componentData' : {
                            'singular' : singular,
                            'plural': plural,
                            'displayed' : 'id',  # component field in Event Console
                            'primaryKey' : 'id',
                            'properties' : {
                                            'eventClass' : getEventClass('/Unknown'),
                                            'productKey' : getProductClass('Unknown'),
                                            # 'productClass' : getReferredMethod('Product', 'getProductClassLink'),
                                            },
                           },
        'createDS' : False,
        'cmdFile' : None,
        'ignoreKeys' : [],
        'datapoints' : [],
        'datasourceMethods' : [],
        'datasourceData' : {'properties': {
                                'timeout' : addProperty('Timeout (s)', 'Timing', 60, ptype='int', switch='-t'),
                                'cycletime' : addProperty('Cycle Time (s)', 'Timing', 300, 'int'),
                                }
                            },

        'fromClass' : "%s.%s.%s" % (root, base, component),
        'saveOld': False,
        'loadOld': False,
        }

class BasicDefinition(object):
    """
        Basic description of CustomComponent and CustomDatasource
    """
    version = None
    zenpackroot = 'ZenPacks.community'  # ZenPack Root
    zenpackbase = None  # ZenaPack Name
    packZProperties = []  # zproperties
    componentMethods = []  # [setFixedPasswords, getFixedPasswords] # list of custom methods to add to CustomComponent class
    componentAttributes = {}  # list of custom attributes for CustomComponent class
    parentClasses = []  # any parent classes besides CustomComponent
    relmgr = None  # CustomRelations()
    addManual = False  # whether CustomComponent can be added from GUI
    component = ''  # name of CustomComponent
    compname = 'os'
    # CustomComponent properties
    componentData = {
                  'singular': '',
                  'plural': '',
                  'displayed': 'id',  # component field in Event Console
                  'primaryKey': 'id',
                  'properties': {
                                 'eventClass' : getEventClass('/Unknown'),
                                 'productKey' : getProductClass('Unknown'),
                                 # 'setfixedpasswords' : getSetter('setFixedPasswords'),
                                 },
                  }
    createDS = False  # whether or not to create CustomDatasource
    cmdFile = None  # reference to script
    ignoreKeys = []  # property ids to ignore when evaluating CustomDatasource getCommand method
    datapoints = []  # expected datapoints output from cmdFile
    datasourceMethods = []  # additional methods to add to CustomDatasource class
    # CustomDatasource properties
    datasourceData = {'properties': {
                                     'timeout' : addProperty('Timeout (s)', 'Timing', 60, ptype='int', switch='-t'),
                                     'cycletime' : addProperty('Cycle Time (s)', 'Timing', 300, 'int'),
                                     }
                      }
    fromClass = "%s.%s.%s" % (zenpackroot, zenpackbase, component)
    saveOld = False
    loadOld = False

    def reset(self):
        '''reset all properties back to their defaults'''
        self.relmgr = CustomRelations()
        self.datasourceData = {'properties': {
                                     'timeout' : addProperty('Timeout (s)', 'Timing', 60, ptype='int', switch='-t'),
                                     'cycletime' : addProperty('Cycle Time (s)', 'Timing', 300, 'int'),
                                     }
                               }
        self.componentData = {
                              'singular': '',
                              'plural': '',
                              'displayed': 'id',  # component field in Event Console
                              'primaryKey': 'id',
                              'properties': {
                                             'eventClass' : getEventClass('/Unknown'),
                                             'productKey' : getProductClass('Unknown'),
                                             # 'setfixedpasswords' : getSetter('setFixedPasswords'),
                                             },
                              }
        self.createDS = False
        self.cmdFile = None
        self.ignoreKeys = []
        self.datapoints = []
        self.datasourceMethods = []
        self.packZProperties = []
        self.componentMethods = []  # [setFixedPasswords, getFixedPasswords]
        self.componentAttributes = {}
        self.parentClasses = []
        self.addManual = False
        self.compname = 'os'
        self.relmgr = CustomRelations()
        self.saveOld = False
        self.loadOld = False

