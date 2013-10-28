from Products.Zuul.utils import ZuulMessageFactory as _t
from Products.ZenModel.ZVersion import VERSION as ZENOSS_VERSION
from Products.ZenUtils.Version import Version
from Products.Zuul.form import schema
from Products.Zuul.infos import ProxyProperty
from ZenPacks.community.ConstructionKit.ClassHelper import stringToMethod

if Version.parse('Zenoss ' + ZENOSS_VERSION) >= Version.parse('Zenoss 4'):
    SingleLineText = schema.TextLine
    MultiLineText = schema.Text
else:
    SingleLineText = schema.Text
    MultiLineText = schema.TextLine

def getEventClass(name):
    '''
        convenience method for event class property
    '''
    return addProperty(title='Event Class', default=name, ptype='selection', isMethod=True, methodName='getEventClasses', isSetter=True)

def getSetter(name):
    '''
        convenience method for property set after modeling
    '''
    return addProperty(title=name, default=name.lower(),  ptype='string', isMethod=True, visible=False, isSetter=True, methodName=name)
 
def getReferredMethod(title, name):
    '''
        convenience method for display property
    '''
    return addProperty(title, name, ptype='string', isMethod=True, optional=False, isReference=True, methodName=name) 

def addProperty(title, group='Basic', default=None, ptype='string', switch=None, optional=True, override=False, 
                isReference=False, order=None, width=120, visible=True, isMethod=False, methodName=None, isSetter=False):
    """
        return dictionary describing component properties
    """
    if optional == 'false':  optional = False
    if optional == 'true':  optional = True
    return CustomProperty(title, group, default, ptype, switch, optional, override, isReference, order, width, visible, isMethod, methodName, isSetter)

class CustomProperty(object):
    ''''''
    id = ''
    ptype = None # type per keys of TYPESCHEMA
    default = None # default value
    title = None # displayed name
    group = None # details grouping
    switch = None # command line parameter switch
    optional = True # whether property MUST exist
    override = False # whether to override with default properties
    isReference = False  # is a reference to another property 
    isText = True # is a text type
    order = None # order on details pane
    visible = True # whether to display in details pane
    isMethod = False #if this is a method
    methodName = ''
    isSetter = False
    width=260
    
    TYPESCHEMA = {
              'string': {'interface': SingleLineText, 'xtype': 'textfield', 'quote': True},
              'lines': {'interface': MultiLineText, 'xtype': 'textarea', 'quote': True},
              'boolean': {'interface': schema.Bool, 'xtype': 'checkbox', 'quote': False},
              'password': {'interface': schema.Password, 'xtype': 'textfield', 'quote': True},
              'int': {'interface': schema.Int, 'xtype': 'textfield', 'quote': False},
              'float': {'interface': schema.Float, 'xtype': 'textfield', 'quote': False},
              'tuple': {'interface': schema.Tuple, 'xtype': 'textarea', 'quote': False},
              'list': {'interface': schema.List, 'xtype': 'textarea', 'quote': False},
              'selection': {'interface': schema.Choice, 'xtype': 'combo', 'quote': False},
              'multichoice': {'interface': schema.MultiChoice, 'xtype': 'combo', 'quote': False},
              'entity': {'interface':  schema.Entity, 'xtype': 'field', 'quote': False},
              'file': {'interface': schema.File, 'xtype': 'field', 'quote': False},
              #'method': {'interface': SingleLineText, 'xtype': 'method', 'quote': False},
              }
    
    TEXTTYPES = ['string','lines','password']
    
    def __init__(self, title, group, default, ptype, switch, optional, override, isReference, order, width, visible, isMethod, methodName, isSetter):
        self.ptype = ptype
        self.default = default
        self.title = title
        self.group = group
        self.switch = switch
        self.optional = optional
        if optional == 'false':  self.optional = False
        if optional == 'true':  self.optional = True
        self.override = override
        self.isReference = isReference
        self.order = order
        self.width = width
        self.visible = visible
        self.isMethod = isMethod
        self.methodName = methodName
        self.isSetter = isSetter
        if self.ptype not in self.TEXTTYPES:  self.isText = False
    
    def get(self):
        return {
            'id'  : self.id,
            'type': self.ptype,
            'default': self.default,
            'title': self.title,
            'group': self.group,
            'switch': self.switch,
            'optional' : self.optional,
            'isReference' : self.isReference,
            'override': self.override,
            'order': self.order
            }
    
    def xtype(self):
        return self.TYPESCHEMA[self.ptype]['xtype']
    
    def interface_type(self):
        try:
            return self.TYPESCHEMA[self.ptype]['interface']
        except:
            return self.TYPESCHEMA['string']['interface']
            
    def quote(self):
        return self.TYPESCHEMA[self.ptype]['quote']
    
    def is_optional(self):
        if self.optional == True:
            return 'true'
        else:
            return 'false'
    
    def get_info(self):
        '''return object suitable for info.py'''
        if self.isMethod == True:
            text = '''@property\ndef %s(self):\n    return self._object.%s()''' % (self.id, self.id)
            return stringToMethod(self.id, text)
        else:
            return ProxyProperty('%s' % self.id)
    
    def get_interface(self):
        '''return object suitable for interfaces.py'''
        if self.isMethod == True:
            if self.isText ==True:
                return self.interface_type()(title=_t(u'%s' % self.title), readonly=True, group=_t(u'%s' % self.group))
            else:
                return None
        if self.order is not None:
            return self.interface_type()(title=_t(u'%s' % self.title), group=_t(u'%s' % self.group), order=self.order)
        else:
            return self.interface_type()(title=_t(u'%s' % self.title), group=_t(u'%s' % self.group))
    
    def get_chooser(self, vocname, vocref, voctext):
        ''''''
        listName = "list%s" % self.methodName
        getName = "_get%s" % self.id
        setName = "_set%s" % self.id
        listChoices = stringToMethod(listName, '''def %s(self):\n    return self._object.%s()\n''' % (listName, self.methodName))
        getChoice = stringToMethod(getName, '''def %s(self):\n    return self._object.%s\n''' % (getName, self.id))
        setChoice = stringToMethod(setName, '''def %s(self, value):\n    self._object.%s = value\n'''% (setName, self.id))
        data = {'info': {}, 'interface': {}, 'infotext': {}}
        data['info'][listName] = listChoices
        data['info'][getName] = getChoice
        data['info'][setName] = setChoice
        data['info'][self.id] = property(getChoice, setChoice)
        #voctext = '''from zope.schema.vocabulary import SimpleVocabulary\ndef %s(context):\n    return SimpleVocabulary.fromValues(context.%s())\n\n''' % (vocname, listName)
        data['infotext'][vocname] = voctext % (vocname, listName)
        data['interface'][self.id] = schema.Choice(title=_t(u'%s' % self.title), alwaysEditable=True, vocabulary=vocref, default=self.default)
        return data
    
    def get_classproperty(self,is_datasource=False):
        '''return object suitable for component/datasource property'''
        data = {
                'id': self.id,
                'type': self.ptype,
                'mode': '',
                'switch': self.switch
                }
        if is_datasource == True:
            data['mode'] = 'w'
        if self.isMethod == True:
            #data['type'] = 'lines'
            data['mode'] = 'w'
        if self.isSetter == True:
            #if self.title == self.id.lower():
            #data['setter'] = self.title
            if self.methodName:
                data['setter'] = self.methodName
            else:
                data['setter'] = self.id
        if self.id == 'eventClass':  data['mode'] = 'w'
        return data
    
    def get_classattribute(self, is_datasource=False):
        '''return object suitable for component/datasource attribute'''
        if is_datasource == False:
            if self.default is not None:
                if self.isReference == True:
                    #return "getattr(here, %s)" % self.default
                    return '${here/%s}' % self.default
                else:
                    #if self.isText ==True:
                    #    #return "'%s'" % self.default
                    #    return "%s" % self.default
                    #else:
                    return "%s" % self.default
            else:
                return self.default
        else:
            if self.id not in ['cycletime','timeout']:
                return '${here/%s}' % self.id
            else:
                return self.default
    
    def get_override(self):
        '''
            text string to override default values within add method
        '''
        if self.override == True:
            if self.isMethod == True:
                return '''component.%s(%s)\n''' % (self.title, self.default)
            else:
                if self.isReference == True: # set the property to a device attribute 
                    return '''setattr(component,"%s",target.%s)\n''' % (self.id, self.default)
                else:  # set the property to the literal value provided
                    if self.isText ==True:
                        return '''setattr(component,"%s","'%s'")\n''' % (self.id, self.default)
                    else:
                        return '''setattr(component,"%s","%s")\n''' % (self.id, self.default)
                
    def jsonAdd(self):
        ''' format fields for the component-add.js file '''
        if self.optional == False:
            return {
                    'xtype' : self.xtype(),
                    'name' : self.id,
                    'fieldLabel' : _t('%s') % self.title,
                    'id' : '%sField' % self.id,
                    'width' : self.width*2 ,
                    'allowBlank' : self.is_optional()
                    }
        return None
        
    def jsonComponentField(self):
        ''' fields for the component.js file '''
        if self.optional == False:
            return {'name': '%s' % self.id}
        return None
    
    def jsonComponentColumn(self):
        '''columns for the component.js file'''
        
        if self.optional == False:
            return {'id': '%s' % self.id,
                    'dataIndex': '%s' % self.id,
                    'header': _t('%s') % self.title,
                    'sortable': 'true',
                    'width': self.width
                    }
        return None
