from Products.ZenModel.OSComponent import OSComponent
from AccessControl import ClassSecurityInfo
from AccessControl import Permissions
from Products.ZenModel.ZenossSecurity import *


from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.ZenModel.ManagedEntity import ManagedEntity
from Products.ZenRelations.RelSchema import *
import logging
log = logging.getLogger('zen.zenhub')

class CustomComponent(OSComponent, ManagedEntity, ZenPackPersistence):
    """
    basic Component class
    """
    
    primaryKey = ''
    nameKey = ''
    portal_type = meta_type = 'CustomComponent'
    isUserCreatedFlag = True
    status=0
    
    _relations = OSComponent._relations #+ (
    
    factory_type_information = (
        {
            'id'             : 'CustomComponent',
            'meta_type'      : 'CustomComponent',
            'description'    : """Arbitrary device grouping class""",
            'icon'           : 'CustomComponent_icon.gif',
            'product'        : 'ZenModel',
            'factory'        : 'manage_addCustomComponent',
            'immediate_view' : 'viewCustomComponent',
            'actions'        :
            (
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'viewCustomComponent'
                , 'permissions'   : (ZEN_VIEW,)
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'perfConf'
                , 'name'          : 'Template'
                , 'action'        : 'objTemplates'
                , 'permissions'   : ("Change Device", )
                },
            )
          },
        )
    
    security = ClassSecurityInfo()
    
    def __init__(self, id, title=None):
        OSComponent.__init__(self, id, title)
        super(CustomComponent, self).__init__(id, title)
    
    def statusMap(self):
        return 0
    
    def getStatus(self):
        return self.statusMap()
    
    def isUserCreated(self):
        return self.isUserCreatedFlag
    
    def primarySortKey(self):
        return getattr(self, self.primaryKey)
    
    def viewName(self):
        return getattr(self, self.nameKey)
    
    name = titleOrId = viewName
    
    def getAssociates(self):
        ''' find objects associated with this one '''
        associates = []
        ignoreKeys = ['dependencies', 'dependents', 'links', 'os']
        for rel in self.getRelationshipNames():
            if rel in ignoreKeys:  continue
            target = getattr(self,rel)
            if target is not None:  associates.append(target)
        return associates
    
    def findDevice(self, match, attribute='manageIp'):
        ''' find Zenoss device matching provided attribute and match'''
        brains = self.getDmd().Devices.deviceSearch()
        return self.findBrainsObject(brains, attribute, match)

    def findDeviceComponent(self, device, classname, attribute, match):
        ''' find Zenoss component matching provided attribute and match'''
        if device:
            brains = device.componentSearch(meta_type=classname)
            return self.findBrainsObject(brains, attribute, match)
        return None
    
    def findComponent(self, classname, attribute, match):
        ''' find Zenoss component matching provided attribute and match'''
        brains = self.getDmd().global_catalog(meta_type=classname)
        return self.findBrainsObject(brains, attribute, match)
    
    def findBrainsObject(self, brains, attribute, match):
        '''find an object in the given catalog (brains) with matching attribute'''
        for b in brains:
            ob = b.getObject()
            if str(match) in str(getattr(ob, attribute)): return ob
            #if str(getattr(ob, attribute)) == str(match):  return ob
        return None
    
    def getEventClasses(self):
        '''return list of event classes'''
        names = []
        for eventClass in self.getDmd().Events.getSubOrganizers():  
            name = eventClass.getOrganizerName()
            if name not in names:  names.append(name)
        return names

    def _setPropValue(self, id, value):
        '''Override from PropertyManager to handle checks and binds'''
        self._wrapperCheck(value)
        setattr(self,id,value)
        self.setCustomProp(id, value)
    
    def setCustomProp(self, id, value):
        '''set object properties after modeler runs'''
        for data in self._properties:
            if id == data['id']:
                action = getattr(ob, data['setter'])
                action()
    
    def getRelatedComponentLink(self, relname, attribute):
        '''Return new-style link to component'''
        try:
            ob = getattr(self, relname, None)()
            return "<a href='%s/devicedetail#deviceDetailNav:%s:%s'>%s</a>" % ( 
                      ob.device().getPrimaryUrlPath(),
                      ob.meta_type,
                      ob.getPrimaryUrlPath(), 
                      getattr(ob, attribute)
                    )
        except:
            return None
        
    def getRelatedDeviceLink(self, relname, attribute):
        ''' get link to zenoss device'''
        device = getattr(self, relname, None)
        if device:
            return device().getDeviceLink()
        else:
            return attribute
    
    def getIpLink(self, attribute):
        '''Return the network link for the given IP'''
        try:
            return self.dmd.Networks.findIp(attribute).getIdLink()
        except:
            return attribute
    
    def unsetCustomRelation(self, relation):
        '''remove custom relation from this component '''
        try:
            rel = getattr(self, relation)
            rel._remoteRemove()
            rel._remove()
        except:
            pass
        
    def setCustomRelation(self, object, torelation, fromrelation):
        ''' add custom relation to this component '''
        if object:
            try:
                torel = getattr(self, torelation)
                fromrel = getattr(object, fromrelation)
                torel._add(object)                
                fromrel._add(self)
            except:
                pass
        
    def removeCustomRelations(self):
        ''' remove custom component relations '''
        diffs = [x for x in self._relations if x not in OSComponent._relations and x[0] != 'os']
        for d in diffs:
            log.debug("unsetting relation: %s" % d[0])
            #print "unsetting relation: %s" % d[0]
            self.unsetCustomRelation(d[0])

    def updateCustomRelations(self):
        ''' update component relations based on setter methods in _properties '''
        ignoreKeys = ['productionState','preMWProductionState','eventClass',]
        self.removeCustomRelations()
        for data in self._properties:
            if data['id'] in ignoreKeys:  continue
            if 'setter' in data.keys():
                action = getattr(self, data['setter'])
                action()
    
    def manage_deleteComponent(self, REQUEST=None):
        ''' Delete OSComponent '''
        url = None
        if REQUEST is not None:
            url = self.device().os.absolute_url()
        self.removeCustomRelations()
        self.getPrimaryParent()._delObject(self.id)
        '''
        eventDict = {
            'eventClass': Change_Remove,
            'device': self.device().id,
            'component': self.id or '',
            'summary': 'Deleted by user: %s' % 'user',
            'severity': Event.Info,
            }
        self.dmd.ZenEventManager.sendEvent(eventDict)
        '''
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(url)
                
    def manage_updateComponent(self, datamap, REQUEST=None):
        '''Update OSComponent'''
        url = None
        if REQUEST is not None:
            url = self.device().os.absolute_url()
        self.updateCustomRelations()
        self.getPrimaryParent()._updateObject(self, datamap)
        '''
        eventDict = {
            'eventClass': Change_Set,
            'device': self.device().id,
            'component': self.id or '',
            'summary': 'Updated by user: %s' % 'user',
            'severity': Event.Info,
            }
        self.dmd.ZenEventManager.sendEvent(eventDict)
        '''
        if REQUEST is not None:
            REQUEST['RESPONSE'].redirect(url)
