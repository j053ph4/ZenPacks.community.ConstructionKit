from Products.ZenRelations.RelSchema import *
import os,re,json,pprint


ZENPACKNAME="ZenPacks.community.ConstructionKit"
# ZenPack files directory
CWD = os.path.dirname(os.path.realpath(__file__))+'/templates' 
#cwd = '/opt/zenoss/local/joseph/ZenPacks.community.ConstructionKit/ZenPacks/community/ConstructionKit'

# component template files
compClass = '%s/%s' % (CWD,"componentClass.txt")
compConfig = '%s/%s' % (CWD,"componentConfigure.txt")
compFacade = '%s/%s' % (CWD,"componentFacade.txt")
compInfo = '%s/%s' % (CWD,"componentInfo.txt")
compInterface = '%s/%s' % (CWD,"componentInterface.txt")
compRouter = '%s/%s' % (CWD,"componentRouter.txt")
# datasource template files
dsClass = '%s/%s' % (CWD,"datasourceClass.txt")
dsConfig = '%s/%s' % (CWD,"datasourceConfigure.txt")
dsInfo = '%s/%s' % (CWD,"datasourceInfo.txt")
dsInterface = '%s/%s' % (CWD,"datasourceInterface.txt")
# JS files
compAddJS = '%s/%s' % (CWD,"js-add.txt")
compShowJS = '%s/%s' % (CWD,"js-show.txt")
# configure.zcml
configZCMLStart = '%s/%s' % (CWD,"configure-start.txt")
configZCMLFinish = '%s/%s' % (CWD,"configure-finish.txt")
# methods
getCommand = '%s/%s' % (CWD,"getcommand.txt")
addMethod = '%s/%s' % (CWD,"addmethod.txt")

# NEED TO VERIFY THE XTYPES ON THESE
TYPESCHEMA = {
              'string': {'interface': 'SingleLineText', 'xtype': 'textfield', 'quote': True},
              'lines': {'interface': 'MultiLineText', 'xtype': 'textarea', 'quote': True},
              'boolean': {'interface': 'schema.Bool', 'xtype': 'checkbox', 'quote': False},
              'password': {'interface': 'schema.Password', 'xtype': 'textfield', 'quote': True},
              'int': {'interface': 'schema.Int', 'xtype': 'textfield', 'quote': False},
              'float': {'interface': 'schema.Float', 'xtype': 'textfield', 'quote': False},
              'tuple': {'interface': 'schema.Tuple', 'xtype': 'textarea', 'quote': False},
              'list': {'interface': 'schema.List', 'xtype': 'textarea', 'quote': False},
              'selection': {'interface': 'schema.Choice', 'xtype': 'combo', 'quote': False},
              'multichoice': {'interface': 'schema.MultiChoice', 'xtype': 'combo', 'quote': False},
              'entity': {'interface':  'schema.Entity', 'xtype': 'field', 'quote': False},
              'file': {'interface': 'schema.File', 'xtype': 'field', 'quote': False},
              }

    
def addProperty(title, group, default=None, ptype='string', switch=None, optional='true', override=False, isReference=False):
    """
        return dictionary describing component properties
    """
    data = {
            'type': ptype,
            'default': default,
            'title': title,
            'group': group,
            'switch': switch,
            'optional' : optional,
            'isReference' : isReference,
            'override': override,
            }
    return data

def stringToMethod(methodName,methodString):
    """
        return a python method given string representing the method
    """
    #printMethod(methodName,methodString)
    data = {}
    exec methodString in data
    return data[methodName]

def printMethod(name,string):
    """
    """
    print "adding method ",name
    print ""
    for r in string.split('\n'):
        print r
    print ""
    
def printFile(name,string):
    ''''''''
    print "adding file ",name
    print ""
    for r in string.split('\n'):
        print r
    print ""

def writeLines(filename,lines,mode="w"):
    """
        write text to file
    """
    print "building file: %s with %s lines" % (filename,len(lines.split('\n')))
    cache = open(filename,mode)
    for line in lines.split('\n'):
        cache.write("%s\n" % line)
    cache.close()

def readLines(filename):
    """
        read lines from file
    """
    cache = open(filename,'r')
    return cache.read()

class Construct():
    
    def __init__(self,d):
        ''''''''
        self.d = d
        try:
            self.createDS = self.d.createDS
        except:
            self.createDS = True
        self.version = self.d.version
        self.cwd = self.d.cwd
        self.zenpackroot = self.d.zenpackroot
        self.zenpackbase = self.d.zenpackbase
        self.zenpackname = "%s.%s" % (self.zenpackroot, self.zenpackbase)
        self.buildComponent()
        if self.createDS == True:
            self.buildDataSource()
        
    def buildComponent(self):
        ''''''
        self.componentClass = self.d.component
        self.componentSingle = self.d.componentData['singular']
        self.componentPlural = self.d.componentData['plural']
        self.props = self.d.componentData['properties']
        self.nameKey = self.d.componentData['displayed']
        self.primaryKey = self.d.componentData['primaryKey']
        self.zenpackComponentModule = "%s.%s" % (self.zenpackname, self.componentClass)
        self.relname = "%s%ss" % (self.componentClass[:1].lower(),self.componentClass[1:])
        #self.componentToDevice = (("os", ToOne(ToManyCont, "Products.ZenModel.OperatingSystem", self.relname)),)
        self.deviceToComponent = ((self.relname, ToManyCont(ToOne, self.zenpackComponentModule, "os")),)
        self.componentJSName = self.componentClass.lower()
        self.override = self.buildOverrides()
        # define class names
        self.infoClass = "%sInfo" % self.componentClass
        self.interfaceClass = "I%s" % self.infoClass
        self.facadeClass = "%sFacade" % self.zenpackbase
        self.iFacadeClass = "I%s" % self.facadeClass
        self.adapterClass = "%sAdapter" % self.zenpackbase
        self.routerClass = "%sRouter" % self.zenpackbase
        self.componentfile = "%s/%s.py" % (self.cwd,self.componentClass)
        self.infofile = "%s/info.py" % self.cwd
        self.interfacefile = "%s/interfaces.py" % self.cwd
        self.facadefile = "%s/facades.py" % self.cwd
        self.routerfile = "%s/routers.py" % self.cwd
        self.migratefile = "%s/migrate/ComponentMigration.py" % self.cwd
        # now set up the properties
        self.setComponentProperties()
        self.buildAddMethods()
    
    def setComponentProperties(self):
        """
            update provided dictionary with class-related data
        """
        self.classAttributes = self.getClassAttributes(self.props)
        self.classProperties = self.getClassProperties(self.props)
        self.infoProperties = self.getInfoProperties(self.props)
        self.interfaceProperties = self.getInterfaceProperties(self.props)
        
    def buildDataSource(self):
        ''''''
        self.datasourceClass = self.componentClass + 'DataSource'
        self.datasourceData = {}
        self.datasourceData['properties'] = {}
        self.datasourceData['properties'].update(self.d.componentData['properties'])
        self.datasourceData['properties']['timeout'] = addProperty('Timeout (s)','Timing',self.d.cycleTime,switch='-t')
        self.datasourceData['properties']['cycletime'] = addProperty('Cycle Time (s)','Timing',self.d.timeout,'int')
        self.datasourceInfo = "%sInfo" % self.datasourceClass
        self.datasourceInterface = "I%s" % self.datasourceInfo
        self.datasourcefile = "%s/datasources/%s.py" % (self.cwd,self.datasourceClass)
        self.setDataSourceProperties()
        
    def setDataSourceProperties(self):
        self.datasourceInfoProperties = self.getInfoProperties(self.datasourceData['properties'])
        self.datasourceInterfaceProperties = self.getInterfaceProperties(self.datasourceData['properties'])
        self.datasourceClassProperties = self.getClassProperties(self.datasourceData['properties'],ds=True)
        self.datasourceClassAttributes = self.getClassAttributes(self.datasourceData['properties'],ds=True)
        self.cycletime = self.datasourceData['properties']['cycletime']['default']
        self.timeout = self.datasourceData['properties']['timeout']['default']
        self.component = "'${here/%s}'" % self.d.componentData['displayed']
        self.cmdFile = "'%s'" % self.d.cmdFile
        self.dpoints = str(self.d.datapoints)
        try:
            self.eventClass = self.datasourceData['properties']['eventKey']['default']
        except:
            self.eventClass = "'/Unknown'"
    
    def buildOverrides(self):
        """
            override component attributes with default properties
        """
        override = '\n'
        for k,v in self.props.items():
            if v['override'] == True:
                if v['isReference'] == True:
                    override += '''    setattr(component,"%s",target.%s)\n''' % (k,v['default'])
                else:
                    override += '''    setattr(component,"%s","%s")\n''' % (k,v['default'])
        return override
    
    def buildAddMethods(self):
        """
            basic add component method
        """
        self.createMethodName = "add%s" % self.componentClass
        self.createMethod = readLines(addMethod) % (self.zenpackname, self.componentClass, self.componentClass,
                                                    self.componentClass, self.relname, self.buildOverrides())
        # device "manage_addComponent" method
        self.addMethodName = "manage_%s" % self.createMethodName
        self.addMethod = """def %s(self, **kwargs):
    target = self
    %s
    return component
""" % (self.addMethodName, self.createMethod)
        # facade "manage_addComponent" method
        self.facadeMethodName = self.createMethodName
        self.facadeMethod = ''
        for line in self.createMethod.split('\n'):
            self.facadeMethod += '    %s\n' % line
        # interface facade "manage_addComponent" method
        self.iFacadeMethodName = self.createMethodName
        self.routerMethodName = "%sRouter" % self.createMethodName

    def getClassAttributes(self,data,ds=False):
        '''
            set class attributes
        '''
        output = ''
        for k,v in data.items():
            isReference = v['isReference']
            
            if ds == False:
                if  v['default'] is not None:
                    if isReference == True:
                        output += """    %s = ''\n""" % k
                    else:
                        output += """    %s = %s\n""" % (k,v['default'])
                else:
                    output += """    %s = %s\n""" % (k,v['default'])
            else:
                if k != 'cycletime' and k != 'timeout' : 
                    output += """    %s = '${here/%s}'\n""" % (k,k)
        return output
    
    def getClassProperties(self,data,ds=False):
        '''
            set class _properties
        '''
        output = ''
        for k,v in data.items():
            if ds == False:
                output += """    {'id': '%s', 'type': '%s','mode': '', 'switch': '%s' },\n""" % (k,v['type'],v['switch'])
            else:
                output += """    {'id': '%s', 'type': '%s','mode': 'w', 'switch': '%s'},\n""" % (k,v['type'],v['switch'])
        return output
    
    def getInfoProperties(self,data):
        '''
            set class info attributes
        '''
        from Products.Zuul.infos import ProxyProperty
        output = ''''''
        for k in data.keys():
            output += """    %s = ProxyProperty('%s')\n""" % (k,k)
        return output
    
    def getInterfaceProperties(self,data):
        '''
            set class interface attributes
        '''
        output = ''''''
        for k,v in data.items():
            dtype = v['type']
            dtitle = u"%s" % v['title']
            schemaclass = TYPESCHEMA[dtype]['interface']
            output += """    %s = %s(title=_t(u'%s'))\n""" % (k,schemaclass,dtitle)
        return output
    
    def writeComponentFiles(self):
        '''
            write Zenpack component files
        '''
        # component class
        lines = readLines(compClass) % (self.componentClass,self.componentClass,self.classAttributes,self.classProperties,self.relname,self.primaryKey,self.nameKey)
        writeLines(self.componentfile,lines)
        # class info
        lines = readLines(compInfo) % (self.zenpackname,self.infoClass,self.interfaceClass,self.infoProperties)
        writeLines(self.infofile,lines)
        # class interface
        lines = readLines(compInterface) % (self.interfaceClass,self.interfaceProperties,self.iFacadeClass,self.iFacadeMethodName)
        writeLines(self.interfacefile,lines)
        # class facade
        lines = readLines(compFacade) % (self.facadeClass,self.componentClass,self.facadeClass,self.iFacadeClass,self.facadeMethodName,self.facadeMethod,self.componentSingle)
        writeLines(self.facadefile,lines)
        # class router
        lines = readLines(compRouter) % (self.routerClass,self.adapterClass,self.routerMethodName,self.createMethodName)
        writeLines(self.routerfile,lines)
    
    def writeDatasourceFiles(self):
        '''
            write Zenpack datasource files
        '''
        # pretty up the component props dict
        proptext = '' # pprint.pformat(self.props,indent=4)
        # datasource class
        lines = readLines(dsClass) % (self.datasourceClass, self.componentClass, self.zenpackname,
                                      self.eventClass, self.cycletime, self.timeout, self.component, self.cmdFile, self.d.provided,
                                      self.dpoints, self.datasourceClassAttributes, self.datasourceClassProperties,
                                      self.datasourceClass,self.datasourceClass,readLines(getCommand))
        writeLines(self.datasourcefile,lines)
        # info
        lines = readLines(dsInfo) % (self.zenpackname,self.zenpackname,self.datasourceClass,
                                     self.componentClass, self.datasourceClass,'onRedirectOptions',
                                     self.datasourceInfo,self.datasourceInterface,self.datasourceInfoProperties)
        writeLines(self.infofile,lines,"a")
        # interfaces
        lines = readLines(dsInterface) % (self.datasourceInterface,self.datasourceInterfaceProperties)
        writeLines(self.interfacefile,lines,"a")
    
    def buildZenPackFiles(self):
        """
            build all files for this zenpack
        """
        self.writeComponentFiles()
        if self.createDS == True:
            self.writeDatasourceFiles()
        self.buildConfigureXML()
        self.buildComponentJS()
        self.buildAddComponentJS()
    
    def buildJavaScriptFiles(self):
        """
            build the component.js and component-add.js files
        """
        # component panel
        filename = "%s/resources/%s.js" % (self.cwd,self.componentJSName)
        jslines = buildComponentJS()
        writeLines(filename,jslines)
        # add component dialog
        filename = "%s/resources/%s-add.js" % (self.cwd,self.componentJSName)
        jslines = buildAddComponentJS()
        writeLines(filename,jslines)
    
    def jsonAddFields(self,data):
        """
            format fields for the component-add.js file
        """
        fields = "["
        for key in data.keys():
            vdata = data[key]
            xtype = TYPESCHEMA[vdata['type']]['xtype']
            if vdata['optional'] == 'false':
                fields += """
                {
                xtype: '%s',
                name: '%s',
                fieldLabel: _t('%s'),
                id: "%sField",
                width: 260,
                allowBlank: %s,
                },
                """ % (xtype,key,vdata['title'],key,vdata['optional'])
        fields += "]"
        return fields
    
    def jsonFields(self,data):
        """
            fields for the component.js file
        """
        import json
        fields = """[
            {name: 'uid'},
            {name: 'severity'},
            {name: 'status'},
            {name: 'name'},"""
        for key in data.keys():
            if data[key]['optional'] == 'false':
                fields += """{name: '%s'},
                """ % key
        fields += """
            {name: 'usesMonitorAttribute'},
            {name: 'monitor'},
            {name: 'monitored'},
            {name: 'locking'},
            ]
        """
        return fields
    
    def jsonColumns(self,data):
        """
            columns for the component.js file
        """
        # determine width of individual columns
        cols = 1
        for key in data.keys():
            if data[key]['optional'] == 'false':
                cols += 1
        # determine width of individual columns
        basewidth = 800/cols
        
        columns = """[{
            id: 'severity',
            dataIndex: 'severity',
            header: _t('Events'),
            renderer: Zenoss.render.severity,
            sortable: true,
            width: 50
        },{
            id: 'name',
            dataIndex: 'name',
            header: _t('Name'),
            sortable: true,
            width: 70
        """
        for key in data.keys():
            if data[key]['optional'] == 'false':
                columns += """},{
                    id: '%s',
                    dataIndex: '%s',
                    header: _t('%s'),
                    sortable: true,
                    width: %s
                """ % (key,key,data[key]['title'],basewidth)
            
        columns += """},{
            id: 'monitored',
            dataIndex: 'monitored',
            header: _t('Monitored'),
            sortable: true,
            width: 65
        },{
            id: 'locking',
            dataIndex: 'locking',
            header: _t('Locking'),
            renderer: Zenoss.render.locking_icons,
            sortable: true,
            width: 65
        }]"""
        return columns
    
    def buildComponentJS(self):
        """
            basic component.js file
        """
        js = readLines(compShowJS) % (
                         self.componentClass,
                         self.componentClass,
                         self.jsonFields(self.props),
                         self.jsonColumns(self.props),
                         self.componentClass,
                         self.componentClass,
                         self.componentClass,
                         self.componentClass,
                         self.componentSingle, 
                         self.componentPlural
                         )
        filename = "%s/resources/%s.js" % (self.cwd,self.componentJSName)
        writeLines(filename,js,"w")
    
    def buildAddComponentJS(self):
        """
            basic component-add.js file
        """
        js = readLines(compAddJS) % (self.componentSingle,
                                     self.componentSingle,
                                     self.jsonAddFields(self.props),
                                     self.zenpackbase,
                                     self.routerClass,
                                     self.routerMethodName,
                                     self.componentSingle
                                     )
        filename = "%s/resources/%s-add.js" % (self.cwd,self.componentJSName)
        writeLines(filename,js,"w")
    
    def buildConfigureXML(self):
        """
            basic configure.zcml file
        """
        text = readLines(configZCMLStart)
        if self.createDS == True:
            text += readLines(dsConfig) % (self.datasourceInfo, self.datasourceClass, self.datasourceClass, 
                                        self.datasourceInterface, self.componentClass, self.componentClass)
        text += readLines(compConfig) % (self.infoClass, self.componentClass, self.componentClass, 
                                         self.interfaceClass, self.zenpackbase, self.routerClass, 
                                         self.adapterClass, self.iFacadeClass, self.facadeClass, 
                                         self.zenpackbase, self.zenpackbase, self.zenpackbase, 
                                         self.componentJSName, self.componentJSName, self.zenpackbase, 
                                         self.componentJSName)
        text += readLines(configZCMLFinish)
        writeLines("%s/configure.zcml" % self.cwd, text, "w")
    
    def addDeviceRelation(self):
        """ Add device relations
        """
        from Products.ZenModel.OperatingSystem import OperatingSystem
        from Products.ZenModel.Device import Device
        OperatingSystem._relations += self.deviceToComponent
        setattr(Device, self.addMethodName, stringToMethod(self.addMethodName, self.addMethod))
        
        

