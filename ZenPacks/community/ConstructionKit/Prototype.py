import logging
log = logging.getLogger('zen.zenhub')
from Products.ZenModel.OperatingSystem import OperatingSystem
from Products.ZenModel.Device import Device
from AccessControl import ClassSecurityInfo, Permissions
from Products.ZenRelations.RelSchema import *
from ZenPacks.community.ConstructionKit.ClassHelper import *
from ZenPacks.community.ConstructionKit.Template import *
from ZenPacks.community.ConstructionKit.CustomProperty import *
from ZenPacks.community.ConstructionKit.CustomRelations import *

from Products.Zuul.utils import ZuulMessageFactory as _t
from zope.schema.vocabulary import SimpleVocabulary

class Prototype():
    '''
        generates and holds all class info prior to class building
    '''
    template = Template()
    add_method = template.ADDMETHOD
    create_method = template.CREATEMETHOD
    facade_method = template.FACADEMETHOD
    ifacade_method = template.IFACADEMETHOD
    router_method = template.ROUTERMETHOD
    override = ''
    
    def __init__(self, root, base, indent=4*' '):
        self.zenpackroot = root
        self.zenpackbase = base
        self.indent = indent
        self.zenpackname = "%s.%s" % (root, base)
        self.relmgr = None#  CustomRelations()
        self.classdata = {
                     'parents' : [CustomComponent],
                     'class': {},
                     'info': {},
                     'interface': {},
                     'facade': {},
                     'ifacade': {},
                     'router': {},
                     'adapter': {},
                     '_properties': [],
                     'infotext': {},
                     'configure': [],

                    }
        
        self.methods = {
                   'create': {'name': None, 'text':None},
                   'add': {'name': None, 'text':None},
                   'facade': {'name': None, 'text':None},
                   'ifacade': {'name': None, 'text':None},
                   'router': {'name': None, 'text':None},
                   'volcab': {'name': None, 'text':None},
                   }
        
    def addComponent(self, name, singular, plural, manual=False, props=[]):
        '''
            collect component info
        '''
        self.is_datasource = False
        self.classname = name
        self.singular = singular
        self.plural = plural
        self.manual = manual
        self.baseid = self.classname.lower()
        self.jsname = self.baseid
        
        self.properties = props
        self.override = ''
        # component relation
        self.relname = "%s%ss" % (self.baseid[:1], self.classname[1:])
        self.helper = ClassHelper(self.classname, self.zenpackbase, self.zenpackroot)
        self.getClassData()
        self.buildAddMethods(self.indent)
    
    def addDataSource(self, name, props=[]):
        '''
            collect datasource info
            
        '''
        self.is_datasource = True
        self.classname = name
        self.properties = props
        self.helper = ClassHelper(self.classname, self.zenpackbase, self.zenpackroot)
        self.getClassData()
        
    def buildAddMethods(self, indent):
        '''
            build the various add_component methods
        '''
        basic_name = "add%s" % self.classname
        basic_text = self.add_method % (self.zenpackname, self.classname, 
                                        self.classname,self.baseid,
                                        self.classname, self.relname, 
                                        self.override)
        # create method
        self.methods['create'] = {'name' : basic_name, 'text' : basic_text }
        # device "manage_addComponent" method
        add_name = "manage_%s" % basic_name
        add_text = self.create_method  % (add_name, basic_text)
        self.methods['add'] = {'name' : add_name, 'text' : add_text}
        # facade "manage_addComponent" method
        facade_name = basic_name
        facade_text = self.facade_method % (facade_name, basic_text, self.singular)
        self.methods['facade'] = {'name' : facade_name, 'text' : facade_text}
        self.classdata['facade'] = self.methods['facade']
        # ifacade method
        ifacade_name = basic_name
        self.methods['ifacade'] = {'name' : ifacade_name, 'text' : self.ifacade_method % ifacade_name}
        self.classdata['ifacade'] = self.methods['ifacade']
        # router method
        router_name = "%sRouter" % basic_name
        self.methods['router'] = {'name' : router_name, 'text' : self.router_method % (router_name, basic_name)}
        self.classdata['router'] = self.methods['router']
    
    def getClassData(self):
        '''
            set class info attributes
        '''
        for p in self.properties:
            if p.isMethod == True and p.ptype == 'selection' and self.is_datasource == False:
                vocref = '%s%s' % (self.classname, p.methodName)
                vocname = "%s%sVocabulary" % (self.classname,p.methodName)
                data = p.get_chooser(vocname, vocref, self.template.COMPONENT_VOLCABULARY_METHOD)
                for k in data.keys(): self.classdata[k].update(data[k])
                self.classdata['configure'] = self.template.CONFIGURE_COMPONENT_VOLCABULARY % (vocname, vocref)
            elif self.is_datasource == True and p.isMethod == True : continue
                #if p.id is not 'eventClass': continue
            else:
                if p.visible == True:
                    self.classdata['info'][p.id] =  p.get_info()
                    self.classdata['interface'][p.id] = p.get_interface()
            self.classdata['class'][p.id] = p.get_classattribute(self.is_datasource)
            self.classdata['_properties'].append(p.get_classproperty(self.is_datasource))
            if p.get_override() is not None:  self.override +=  "%s%s" % (self.indent,p.get_override())
    
    def getHelper(self):
        '''
            build component and datasource classes
        '''
        log.debug( "building %s" % self.helper.classname)
        if self.is_datasource == False:
            #log.debug( self.classdata['class'])
            self.helper.componentClass(self.classdata['parents'], self.classdata['class'])
            self.helper.classobject._relations += tuple(self.relmgr.fromrelations)
            self.helper.classobject._properties += tuple(self.classdata['_properties'])
            
            self.helper.classobject.factory_type_information = (
                {
                    'id'             : '%s' % self.classname,
                    'meta_type'      : '%s' % self.classname,
                    'description'    : """Arbitrary device grouping class""",
                    'icon'           : 'FileSystem_icon.gif',
                    'product'        : '%s' % self.zenpackbase,
                    'factory'        : '%s'  % self.methods['add']['name'],
                    'immediate_view' : 'view%s' % self.classname,
                    'actions'        :
                    (
                        { 'id'            : 'status'
                        , 'name'          : 'Status'
                        , 'action'        : 'view%s'  % self.classname
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

            #self.helper.classobject.isUserCreatedFlag = self.manual
            self.helper.classobject.isUserCreatedFlag = True
            self.helper.interfaceClass(self.classdata['interface'])            
            self.helper.infoClass(self.classdata['info'])
            self.helper.ifacadeClass(self.classdata['ifacade'])            
            self.helper.facadeClass(self.classdata['facade'])            
            self.helper.routerClass(self.classdata['router'])
            self.helper.addClassTextMethod(Device,self.methods['add']['name'], self.methods['add']['text'])
        else:
            self.classdata['class']['factory_type_information'] = ({'immediate_view' : 'edit%s' % self.classname,
                                                                    'actions' : ({
                                                                                  'id' : 'edit',
                                                                                  'name' : 'Data Source',
                                                                                  'action' : 'edit%s' % self.classname,
                                                                                  'permissions'   : ( Permissions.view, ),
                                                                                  },)
                                                                    },)
            self.helper.datasourceClass(self.classdata['class'])
            self.helper.classobject._properties += tuple(self.classdata['_properties'])
            self.helper.interfaceClass(self.classdata['interface'], True)            
            self.helper.infoClass(self.classdata['info'], True)    


