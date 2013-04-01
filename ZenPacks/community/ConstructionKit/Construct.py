from Products.ZenRelations.RelSchema import *
import os,re,json,pprint,errno


ZENPACKNAME="ZenPacks.community.ConstructionKit"
# ZenPack files directory
CWD = os.path.dirname(os.path.realpath(__file__))+'/templates' 
#cwd = '/opt/zenoss/local/joseph/ZenPacks.community.ConstructionKit/ZenPacks/community/ConstructionKit'

# component template files
compClass = '%s/%s' % (CWD,"componentClass.txt")
compConfig = '%s/%s' % (CWD,"componentConfigure.txt")
compConfigAdd = '%s/%s' % (CWD,"componentConfigureAdd.txt")
compFacade = '%s/%s' % (CWD,"componentFacade.txt")
compFacadeMethod = '%s/%s' % (CWD,"componentFacadeMethod.txt")
compInfo = '%s/%s' % (CWD,"componentInfo.txt")
compInterface = '%s/%s' % (CWD,"componentInterface.txt")
compInterfaceClass = '%s/%s' % (CWD,"componentInterfaceClass.txt")
compInterfaceFacade = '%s/%s' % (CWD,"componentInterfaceFacade.txt")
compInterfaceFacadeMethod = '%s/%s' % (CWD,"componentInterfaceFacadeMethod.txt")
compRouter = '%s/%s' % (CWD,"componentRouter.txt")
compRouterMethod = '%s/%s' % (CWD,"componentRouterMethod.txt")
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

TEXTTYPES = ['string','lines','password']

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'w').close()

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

def writeLines(filename,lines,new=True):
    """
        write text to file
    """
    #print "building file: %s with %s lines" % (filename,len(lines.split('\n')))
    if new == True:
        cache = open(filename,'w')
    else:
        cache = open(filename,'a')
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
        try:
            self.addManual = self.d.addManual
        except:
            self.addManual = True
        try:
            self.cycletime = self.d.cycletime
        except:
            self.cycletime = 300
        try:
            self.timeout = self.d.timeout
        except:
            self.timeout = 60
        try:
            self.provided = self.d.provided
        except:
            self.provided = False
             
        self.configZCMLEnded = True
        self.version = self.d.version
        self.cwd = self.d.cwd
        self.zenpackroot = self.d.zenpackroot
        self.zenpackbase = self.d.zenpackbase
        self.zenpackname = "%s.%s" % (self.zenpackroot, self.zenpackbase)
        self.buildComponent()
        if self.createDS == True:
            self.datasourceClass = self.componentClass + 'DataSource'
            self.buildDataSource()
        # ensure all needed directories exist with a __init__.py file
        directories = ['datasources','migrate','objects','resources','modeler','libexec','modeler/plugins']
        for d in directories:
            pathname = "%s/%s" % (self.cwd,d)
            make_sure_path_exists(pathname)
            if d  not in ['resources','skins','objects']:
                touch("%s/__init__.py" % pathname)
        # copy componentMigrate to new dir
        
    def buildComponent(self):
        ''''''
        self.componentClass = self.d.component
        self.baseid = self.componentClass.lower()
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
        #self.createFiles()
        # now set up the properties
        self.classAttributes = self.getClassAttributes(self.props)
        self.classProperties = self.getClassProperties(self.props)
        self.infoProperties = self.getInfoProperties(self.props)
        self.interfaceProperties = self.getInterfaceProperties(self.props)
        # build the add methods
        self.buildAddMethods()
    
    def createFiles(self,new=True):
        ''''''
        self.componentfile = "%s/%s.py" % (self.cwd,self.componentClass)
        self.infofile = "%s/info.py" % self.cwd
        self.interfacefile = "%s/interfaces.py" % self.cwd
        self.facadefile = "%s/facades.py" % self.cwd
        self.routerfile = "%s/routers.py" % self.cwd
        #self.migratefile = "%s/migrate/ComponentMigration.py" % self.cwd

        if new == True:
            touch(self.componentfile)
            touch(self.infofile)
            touch(self.interfacefile)
            touch(self.facadefile)
            touch(self.routerfile)
            #touch(self.migratefile)
        if self.createDS == True:
            self.datasourcefile = "%s/datasources/%s.py" % (self.cwd,self.datasourceClass)
            touch(self.datasourcefile)
        
    def buildDataSource(self):
        ''''''
        self.datasourceData = {}
        self.datasourceData['properties'] = {}
        self.datasourceData['properties'].update(self.d.componentData['properties'])
        self.datasourceData['properties']['timeout'] = addProperty('Timeout (s)','Timing',self.cycletime,switch='-t')
        self.datasourceData['properties']['cycletime'] = addProperty('Cycle Time (s)','Timing',self.timeout,'int')
        self.datasourceInfo = "%sInfo" % self.datasourceClass
        self.datasourceInterface = "I%s" % self.datasourceInfo
        # datasource properties
        self.datasourceInfoProperties = self.getInfoProperties(self.datasourceData['properties'])
        self.datasourceInterfaceProperties = self.getInterfaceProperties(self.datasourceData['properties'])
        self.datasourceClassProperties = self.getClassProperties(self.datasourceData['properties'],ds=True)
        self.datasourceClassAttributes = self.getClassAttributes(self.datasourceData['properties'],ds=True)
        self.component = "'${here/%s}'" % self.d.componentData['displayed']
        try:
            self.cmdFile = "'%s'" % self.d.cmdFile
        except:
            self.cmdFile = None
        try:
            self.dpoints = str(self.d.datapoints)
        except:
            self.dpoints = str([])
        try:
            self.eventClass = self.datasourceData['properties']['eventKey']['default']
        except:
            self.eventClass = '/Unknown'
    
    def buildOverrides(self):
        """
            override component attributes with default properties
        """
        override = '\n'
        for k,v in self.props.items():
            if v['override'] == True:
                if v['isReference'] == True: # set the property to a device attribute 
                    override += '''    setattr(component,"%s",target.%s)\n''' % (k,v['default'])
                else:  # set the property to the literal value provided
                    #if v['type'] == 'string':
                    if v['type'] in TEXTTYPES:
                        override += '''    setattr(component,"%s","'%s'")\n''' % (k,v['default'])
                    else:
                        override += '''    setattr(component,"%s","%s")\n''' % (k,v['default'])
        return override
    
    def buildAddMethods(self):
        """
            basic add component method
        """
        self.createMethodName = "add%s" % self.componentClass
        self.createMethod = readLines(addMethod) % (self.zenpackname, self.componentClass, self.componentClass,self.baseid,
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
                        if v['type'] in TEXTTYPES:
                            output += """    %s = '%s'\n""" % (k,v['default'])
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
    
    def writeComponentFiles(self, new=True):
        '''
            write Zenpack component files
        '''
        # component class
        lines = readLines(compClass) % (self.componentClass,self.componentClass,self.classAttributes,self.classProperties,self.relname,self.primaryKey,self.nameKey)
        writeLines(self.componentfile,lines,new)
        # class info
        lines = readLines(compInfo) % (self.zenpackname,self.infoClass,self.interfaceClass,self.infoProperties)
        writeLines(self.infofile, lines, new)
        # class interface
        if new == True:
            writeLines(self.interfacefile, readLines(compInterface), new)
        # interface component class
        lines = readLines(compInterfaceClass) % (self.interfaceClass,self.interfaceProperties)
        writeLines(self.interfacefile, lines, False)

        # write facade class methods to temp file
        if new == True:
            lines = readLines(compInterfaceFacade) % (self.iFacadeClass)
            writeLines("/tmp/interface-temp", lines, new)
        
        lines = readLines(compInterfaceFacadeMethod) % (self.iFacadeMethodName)
        writeLines("/tmp/interface-temp", lines, False)
        # then write back to main file when done
        if self.configZCMLEnded == True:
            # interface component facade method
            lines = readLines("/tmp/interface-temp")
            writeLines(self.interfacefile, lines, False)
        
        # class facade
        if new == True:
            #lines = readLines(compFacade) % (self.facadeClass,self.componentClass,self.facadeClass,self.iFacadeClass,self.facadeMethodName,self.facadeMethod,self.componentSingle)
            lines = readLines(compFacade) % (self.facadeClass,self.componentClass,self.facadeClass,self.iFacadeClass)
            writeLines(self.facadefile, lines, new)
        # facade method
        lines = readLines(compFacadeMethod) % (self.facadeMethodName,self.facadeMethod,self.componentSingle)
        writeLines(self.facadefile, lines, False)
        
        # class router
        if new == True:
            lines = readLines(compRouter) % (self.routerClass,self.adapterClass)
            writeLines(self.routerfile,lines, new)
            
        lines = readLines(compRouterMethod) % (self.routerMethodName,self.createMethodName)
        writeLines(self.routerfile, lines, False)
        
    def writeDatasourceFiles(self, new=True):
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
        writeLines(self.infofile, lines, new=False)
        # interfaces
        lines = readLines(dsInterface) % (self.datasourceInterface,self.datasourceInterfaceProperties)
        writeLines(self.interfacefile, lines, new=False)
    
    def buildZenPackFiles(self, new=True):
        """
            build all files for this zenpack
        """
        self.createFiles(new)
        self.writeComponentFiles(new)
        if self.createDS == True:
            self.writeDatasourceFiles(new)
        self.buildConfigureXML(new)
        self.buildComponentJS()
        if self.addManual == True:
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
        writeLines(filename,js)
    
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
        writeLines(filename,js)
    
    def buildConfigureXML(self, new=True):
        """
            basic configure.zcml file
        """
        text = ''
        # top part of zcml file
        if new == True:
            text += readLines(configZCMLStart) % (self.zenpackbase, self.routerClass, self.adapterClass, 
                                                  self.iFacadeClass, self.facadeClass, self.zenpackbase)
            writeLines("%s/configure.zcml" % self.cwd, text)
            
        # datasource info
        if self.createDS == True:
            text += readLines(dsConfig) % (self.datasourceInfo, self.datasourceClass, self.datasourceClass, 
                                        self.datasourceInterface, self.componentClass, self.componentClass)
        # component info
        text += readLines(compConfig) % (self.infoClass, self.componentClass, self.componentClass, self.interfaceClass, 
                                         self.componentClass, self.zenpackbase, self.componentJSName)
        if self.addManual == True:
            text += readLines(compConfigAdd) % (self.componentJSName, self.zenpackbase, self.componentJSName)
            
        if self.configZCMLEnded == True:
            text += readLines(configZCMLFinish)
        writeLines("%s/configure.zcml" % self.cwd, text, new)
    
    def addDeviceRelation(self):
        """ Add device relations
        """
        from Products.ZenModel.OperatingSystem import OperatingSystem
        from Products.ZenModel.Device import Device
        OperatingSystem._relations += self.deviceToComponent
        setattr(Device, self.addMethodName, stringToMethod(self.addMethodName, self.addMethod))
        
        

