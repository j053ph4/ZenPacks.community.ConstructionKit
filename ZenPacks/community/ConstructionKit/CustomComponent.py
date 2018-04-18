from collections import OrderedDict
from Products.ZenModel.OSComponent import OSComponent
from Products.ZenModel.DeviceHW import DeviceHW
from Products.ZenModel.MEProduct import MEProduct
from AccessControl import ClassSecurityInfo
from AccessControl import Permissions
from Products.ZenModel.ZenossSecurity import *
from Products.DataCollector.ApplyDataMap import ApplyDataMap

from Products.ZenRelations.ZenPropertyManager import ZenPropertyManager
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenRelations.RelSchema import *
from Products.ZenRelations.Exceptions import *
from ZenPacks.zenoss.ZenPackLib.lib.base.ClassProperty import ClassProperty

from transaction import commit

import logging
log = logging.getLogger('zen.zenhub')

import re
import difflib

from md5 import md5
# put here to fix broken imports from zenpacks after 4.2.4
def getProcessIdentifier(name, parameters):
    """
        Get a process identifier string from the name and parameters of the process.
        This method was used in Zenoss versions prior to 4.2.4
    """
    return ('%s %s' % (name, md5((parameters or '').strip()).hexdigest())).strip()


class CustomComponent(OSComponent, ManagedEntity, MEProduct, ZenPackPersistence):
    '''Basic Class for ConstructionKit-based components'''

    primaryKey = ''
    nameKey = ''
    productKey = 'Unknown'
    portal_type = meta_type = 'CustomComponent'
    isUserCreatedFlag = True
    status = 0
    compname = 'os'
    _v_local_relations = OSComponent._relations + (
        ("productClass", ToOne(ToMany, "Products.ZenModel.ProductClass", "instances")),
    )

    factory_type_information = (
        {'id' : 'CustomComponent',
         'meta_type': 'CustomComponent',
         'description': "Arbitrary device grouping class",
         'icon' : 'CustomComponent_icon.gif',
         'product' : 'ZenModel',
         'factory' : 'manage_addCustomComponent',
         'immediate_view' : 'viewCustomComponent',
         'actions' : ({'id' : 'status', 'name' : 'Status', 'action' : 'viewCustomComponent', 'permissions': (ZEN_VIEW,)},
                       {'id' : 'events', 'name' : 'Events', 'action' : 'viewEvents', 'permissions' : (ZEN_VIEW,)},
                       {'id' : 'perfConf', 'name' : 'Template', 'action' : 'objTemplates', 'permissions' : ("Change Device",)},
                      )
         },
        )

    security = ClassSecurityInfo()

    def __init__(self, id, title=None):
        OSComponent.__init__(self, id, title)
        MEProduct.__init__(self, id, title)
        super(CustomComponent, self).__init__(id, title)

    '''
    required built-ins
    '''
    @ClassProperty
    @classmethod
    def _relations(cls):
        """Return _relations property

        This is implemented as a property method to deal with cases
        where ZenPacks loaded after ours in easy-install.pth monkeypatch
        _relations on one of our base classes.

        """

        relations = OrderedDict()
        for base in cls.__bases__:
            base_relations = getattr(base, '_relations', [])
            for base_name, base_schema in base_relations:
                # In the case of multiple bases having relationships
                # by the same name, we want to use the first one.
                # This is consistent with Python method resolution
                # order.
                relations.setdefault(base_name, base_schema)

        if hasattr(cls, '_v_local_relations'):
            for local_name, local_schema in cls._v_local_relations:
                # In the case of a local relationship having a
                # relationship by the same name as one of the bases, we
                # use the local relationship.
                relations[local_name] = local_schema

        return tuple(relations.items())

    def statusMap(self): return 0

    def getStatus(self): return self.statusMap()

    def isUserCreated(self): return self.isUserCreatedFlag

    def primarySortKey(self): return getattr(self, self.primaryKey)

    def viewName(self): return getattr(self, self.nameKey)

    name = titleOrId = viewName

    ''' 
    functions for purposes of dealing with passwords
    '''
    def encrypt(self, value):
        # log.debug("encrypt: %s" % value)
        return value

    def decrypt(self, value):
        # log.debug("decrypt: %s" % value)
        return value

    def getPassword(self, id):
        '''pass through for later override'''
        # log.debug('basic getPassword for %s on %s' % (id,self.id))
        val = getattr(self, id, None)
        if val is not None:  return self.decrypt(val)
        return None

    def setPassword(self, id, value):
        '''pass through for later override'''
        # log.debug('basic setPassword for %s on %s' % (id,self.id))
        self._setPropValue(id, value)
        commit()

    def setFixedPasswords(self, id=''):
        '''setter method'''
        log.debug('setFixedPasswords on %s' % self.id)
        for prop in self._properties:
            prop_id = prop['id']
            if self.getPropertyType(prop_id) == 'password':
                log.debug("setting fixed passwor to %s" % self.getPassword(prop_id))
                ZenPropertyManager._setPropValue(self, prop_id, self.getPassword(prop_id))

    def getFixedPasswords(self): pass

    ''' 
    functions for returning info to GUI
    '''

    def getEventClasses(self):
        '''return list of event classes'''
        names = []
        for eventClass in self.getDmd().Events.getSubOrganizers():
            name = eventClass.getOrganizerName()
            if name not in names:  names.append(name)
        return names

    def getRelatedComponentLink(self, relname, attribute):
        '''Return new-style link to component'''
        try:
            ob = getattr(self, relname, None)()
            path = '%s/devicedetail#deviceDetailNav:%s:%s' % (ob.device().getPrimaryUrlPath(), ob.meta_type, ob.getPrimaryUrlPath())
            return '<a class="z-entity" href="%s">%s</a>' % (path, getattr(ob, attribute))
        except: return None

    def getRelatedDeviceLink(self, relname, attribute):
        ''' get link to zenoss device'''
        device = getattr(self, relname, None)
        if device:  return device().getDeviceLink()
        else: return attribute

    def getIpLink(self, attribute):
        '''Return the network link for the given IP'''
        try: return self.dmd.Networks.findIp(attribute).getIdLink()
        except: return attribute

    def getProductClassLink(self):
        '''return list of event classes'''
        try:
            ob = getattr(self, 'productClass', None)()
            return ob.getPrimaryLink()
            # path ='%s/devicedetail#deviceDetailNav:%s:%s' % (ob.device().getPrimaryUrlPath(), ob.meta_type, ob.getPrimaryUrlPath())
            # return '<a class="z-entity" href="%s">%s</a>' % (path, getattr(ob, attribute))
        except: return 'None'

    '''
    functions for purposes of finding associated devices/components/objects
    '''

    def getAssociates(self):
        ''' find objects associated with this one '''

        def isOSComponent(obj):
            '''determine if object is a descendant of OSComponent class'''
            import inspect
            klass = obj.__class__
            for b in inspect.getmro(klass):
                if b.__name__ == 'OSComponent': return True
            return False
        # get a list of associated objects, making sure they are device components
        associates = []
        for rel in self.getRelationshipNames():
            try: target = getattr(self, rel)()
            except: target = None
            if target is not None:
                if type(target) == list:
                    for t in target:
                        if isOSComponent(t) is True: associates.append(t)
                else:
                    if isOSComponent(target) is True: associates.append(target)
        return associates

    def findDevice(self, match, attribute='manageIp'):
        ''' find Zenoss device matching provided attribute and match'''
        log.debug('findDevice on %s matching %s: %s' % (self.id, attribute, match))
        # print 'findDevice on %s matching %s: %s' % (self.id, attribute, match)
        brains = self.getDmd().Devices.deviceSearch()
        dev = self.findBrainsObject(brains, attribute, match, .95)
        if dev is None and attribute in ['id', 'title', 'name']:
            for b in brains:
                ob = b.getObject()
                if str(match) in str(getattr(ob, attribute, None)): return ob
        else: return dev

    def findDeviceComponent(self, device, classname, attribute, match):
        ''' find Zenoss component matching provided attribute and match'''
        if device is not None:
            log.debug('findDeviceComponent on %s matching %s: %s: %s: %s' % (self.id, device.id, classname, attribute, match))
            brains = device.componentSearch(meta_type=classname)
            return self.findBrainsObject(brains, attribute, match)
        return None

    def findComponent(self, classname, attribute, match):
        ''' find Zenoss component matching provided attribute and match'''
        log.debug('findComponent on %s for %s matching %s: %s' % (self.id, classname, attribute, match))
        brains = self.getDmd().global_catalog(meta_type=classname)
        return self.findBrainsObject(brains, attribute, match)

    def findBrainsObject(self, brains, attribute, match, cutoff=.8):
        '''find an object in the given catalog (brains) with matching attribute'''
        log.debug('findBrainsObject on %s matching %s: %s' % (self.id, attribute, match))
        # build a dictionary of match attributes and corresponding objects
        # log.debug("CustomComponent findBrainsObject")
        matchers = {}
        for b in brains:
            ob = b.getObject()
            matcher = getattr(ob, attribute)
            if type(matcher) == list:  matcher = ' '.join(matcher)
            matchers[str(matcher)] = ob
        # find the closest matching attribute (by score) in the list of them
        bestMatch = self.closestMatch(str(match), matchers.keys(), cutoff)
        # look for a substring match if the scored match finds nothing
        if bestMatch is None:
            for k, v in matchers.items():
                if str(match) in str(k):
                    log.debug("returning direct match for %s:%s as %s" % (match, k, v.id))
                    return v
        elif bestMatch in matchers.keys():
            log.debug("returning best score: %s" % matchers[bestMatch].id)
            return matchers[bestMatch]
        else:
            log.debug("returning none")
            return None

    def closestMatch(self, match, matchlist, cutoff=.8):
        '''return the closest matching string given a list of strings'''
        log.debug("CustomComponent closestMatch matching %s in %s" % (match, ','.join(matchlist)))
        score = 0
        best = None
        for m in matchlist:
            r = difflib.SequenceMatcher(None, match, m).ratio()
            if r > score:
                score = r
                best = m
        if score > cutoff:
            log.debug('best match for %s is %s with best score: %s' % (match, best, score))
            return best
        else: return None

    ''' 
    functions for manipulating component relations
    '''

    def unsetCustomRelation(self, relation):
        '''remove custom relation from this component '''
        log.debug('unsetCustomRelation %s on %s' % (self.id, relation))
        try:
            rel = getattr(self, relation)
            rel._remoteRemove()
            rel._remove()
        except:  log.warn("problem unsetting relation %s on %s" % (relation, self.id))

    def setCustomRelation(self, object, torelation, fromrelation):
        ''' add custom relation to this component '''
        if object is not None:
            log.debug('setCustomRelation from %s (%s) to: %s (%s)' % (self.id, torelation, object.id, fromrelation))
            # print 'setCustomRelation from %s (%s) to: %s (%s)' % (self.id, torelation, object.id, fromrelation)
            try:
                log.debug('attempting to set relation from %s to: %s)' % (torelation, fromrelation))
                torel = getattr(self, torelation)
                fromrel = getattr(object, fromrelation)
                torel._add(object)
                fromrel._add(self)
            except RelationshipExistsError:
                log.warn("relation exists...resetting relation on %s:%s from %s to %s" % (self.id, object.id, fromrelation, torelation))
                # self.unsetCustomRelation(torelation)
                torel = getattr(self, torelation)
                fromrel = getattr(object, fromrelation)
                try: torel._remove(object)
                except:
                    log.warn("error removing torel")
                    # pass
                try: fromrel._remove(self)
                except:
                    log.warn("error removing fromrel")
                    pass
                try: self.setCustomRelation(object, torelation, fromrelation)
                except: log.warn("problem resetting relation on %s:%s from %s to %s" % (self.id, object.id, fromrelation, torelation))
            except: log.warn("problem setting relation on %s:%s from %s to %s" % (self.id, object.id, fromrelation, torelation))

    def removeCustomRelations(self):
        ''' remove custom component relations '''
        log.debug('removeCustomRelations on %s' % self.id)
        diffs = [x for x in self._relations if x not in OSComponent._relations and x[0] != self.compname]
        for d in diffs:
            log.debug("unsetting relation: %s" % d[0])
            self.unsetCustomRelation(d[0])

    def updateCustomRelations(self):
        ''' update component relations based on setter methods in _properties '''
        log.debug('updateCustomRelations on %s' % self.id)
        ignoreKeys = ['productionState', 'preMWProductionState', 'eventClass', 'productKey']
        self.removeCustomRelations()
        for data in self._properties:
            if data['id'] in ignoreKeys:  continue
            if 'setter' in data.keys():
                action = getattr(self, data['setter'])
                action()
        self.setFixedPasswords()

    ''' 
    overridden built-ins
    '''

    def _setPropValue(self, id, value):
        '''
            Override from PropertyManager to 
            handle checks and binds
            Used by modeler.
        '''
        log.debug('_setPropValue object:%s property:%s value:%s' % (self.id, id, value))
        if self.getPropertyType(id) == 'password':
            self._wrapperCheck(value)
            log.debug("found password type for %s on %s" % (id, self.id))
            ZenPropertyManager._setPropValue(self, id, self.encrypt(value))
        else: ZenPropertyManager._setPropValue(self, id, value)

    def manage_deleteComponent(self, REQUEST=None):
        ''' Delete OSComponent from GUI or CLI'''
        log.debug('manage_deleteComponent: %s' % self.id)
        url = None
        if REQUEST is not None: url = getattr(self.device(), self.compname).absolute_url()
        self.removeCustomRelations()
        self.getPrimaryParent()._delObject(self.id)
        if REQUEST is not None:  REQUEST['RESPONSE'].redirect(url)

    def manage_updateComponent(self, datamap, REQUEST=None):
        '''Update OSComponent from GUI or CLI'''
        log.debug('manage_updateComponent: %s' % self.id)
        url = None
        if REQUEST is not None:  url = getattr(self.device(), self.compname).absolute_url()
        self.updateCustomRelations()
        datamap = self.updateDataMap(datamap)
        self.getPrimaryParent()._updateObject(self, datamap)
        if REQUEST is not None:  REQUEST['RESPONSE'].redirect(url)

    def updateDataMap(self, datamap):
        '''pass-through for later override'''
        log.debug("updateDataMap for %s: %s" % (self.id, datamap))
        return datamap

    ''' 
    functions for setting productClass
    '''

    def setProduct(self, productName, manufacturer="Unknown",
                    newProductName="", REQUEST=None, **kwargs):
        """Set the product class of this software.
        """
        if not manufacturer: manufacturer = "Unknown"
        if newProductName: productName = newProductName
        prodobj = self.getDmdRoot("Manufacturers").createSoftwareProduct(
                                    productName, manufacturer, **kwargs)
        self.productClass.addRelation(prodobj)
        if REQUEST:
            messaging.IMessageSender(ob).sendToBrowser(
                'Product Set',
                ("Set Manufacturer %s and Product %s."
                                    % (manufacturer, productName))
            )
            return self.callZenScreen(REQUEST)

    def setProductKey(self, prodKey, manufacturer=None):
        """Set the product class of this software by its productKey.
        """
        log.debug("setProductKey on %s" % (self.id))
        if prodKey:
            # Store these so we can return the proper value from getProductKey
            self._prodKey = prodKey
            self._manufacturer = manufacturer
            if manufacturer is None:
                manufacturer = 'Unknown'
            manufs = self.getDmdRoot("Manufacturers")
            prodobj = manufs.createSoftwareProduct(prodKey, manufacturer)
            self.productClass.addRelation(prodobj)
            # set product key for assocated components
            for a in self.getAssociates():
                print "found assoc: %s" % a.id
                if a.meta_type in ['OSProcess', 'IpService', 'WinService']:
                    a.productClass.addRelation(prodobj)
            # self.setAssociatedProductKey()
        else:
            self.productClass.removeRelation()

    def setAssociatedProductKey(self):
        """ Set the productClass relation for associated OSProcess, 
            IpService, and WinService components
        """
        log.debug("setAssociatedProductKey on %s" % (self.id))
        product = self.getProductKey()
        for a in self.getAssociates():
            if a.meta_type in ['OSProcess', 'IpService', 'WinService']:
                log.debug("setting product key for %s to %s" % (a.id, product))
                a.setProductKey(product)

class CustomHWComponent(DeviceHW, CustomComponent):
    '''for components with hw relation'''

    primaryKey = ''
    nameKey = ''
    portal_type = meta_type = 'CustomHWComponent'
    isUserCreatedFlag = True
    status = 0
    compname = 'hw'
    _v_local_relations = DeviceHW._relations

    factory_type_information = (
        {'id' : 'CustomHWComponent',
         'meta_type': 'CustomHWComponent',
         'description': "Arbitrary device grouping class",
         'icon' : 'CustomComponent_icon.gif',
         'product' : 'ZenModel',
         'factory' : 'manage_addCustomComponent',
         'immediate_view' : 'viewCustomComponent',
         'actions' : ({'id' : 'status', 'name' : 'Status', 'action' : 'viewCustomComponent', 'permissions': (ZEN_VIEW,)},
                       {'id' : 'events', 'name' : 'Events', 'action' : 'viewEvents', 'permissions' : (ZEN_VIEW,)},
                       {'id' : 'perfConf', 'name' : 'Template', 'action' : 'objTemplates', 'permissions' : ("Change Device",)},
                      )
         },
        )

    security = ClassSecurityInfo()
    def __init__(self, id, title=None):
        CustomComponent.__init__(self, id, title)
        DeviceHW.__init__(self, id, title)
        super(CustomHWComponent, self).__init__(id, title)

