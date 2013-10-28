import logging,os,re,json,errno
from Products.Zuul.utils import ZuulMessageFactory as _t

from ZenPacks.community.ConstructionKit.Template import *
log = logging.getLogger('zen.zenhub')

class ZenPackBuilder(object):
    ''''''
    template = Template()
    # directory containing templates
    js_columns_start = template.JS_COLUMNS_START
    js_columns_finish = template.JS_COLUMNS_FINISH
    js_add_start = template.JS_ADD_START
    js_add_finish = template.JS_ADD_FINISH
    js_display = template.JS_DISPLAY
    js_add = template.JS_ADD
    
    configure_start = template.CONFIGURE_START
    configure_zenpack = template.CONFIGURE_ZENPACK
    configure_finish = template.CONFIGURE_FINISH
    configure_component = template.CONFIGURE_COMPONENT
    configure_component_add = template.CONFIGURE_COMPONENT_ADD
    configure_datasource = template.CONFIGURE_DATASOURCE
    
    init_text = template.INIT_TEXT
    configure_xml = ''
    info_text = ''
    interfaces_text = ''
    facades_text = ''
    routers_text = ''
    vocabulary_method = template.VOCABULARYMETHOD
    construct_import = template.CONSTRUCT_IMPORT
    base_class = template.BASE_CLASS
    add_class = template.ADD_CLASS
    zenpackdir = ''
    zenpackdirectories = ['datasources','migrate','objects','resources','modeler','libexec','modeler/plugins', 'lib']
    zenpackfiles = ['info.py', 'interfaces.py', 'routers.py', 'facades.py']
    
    helpers = {}
    modpath = {}
    files = []
    zenpack = None
    indent = 4*' '
    
    def __init__(self, zenpackdir, zenpackname, indent):
        ''''''
        self.zenpackdir = zenpackdir
        self.zenpackname = zenpackname
        self.indent = indent
        self.helpers = {}
        self.files = []
    
    def addHelper(self, name, definition):
        #log.debug( "adding %s to %s" % (name,self.helpers.keys())
        self.helpers[name] = {'component': None, 'datasource': None, 'definition': definition}
    
    def buildClassFiles(self, helper):
        ''' build class files for component and/or datasource'''
        
        self.files.append({'name': "%s/%s.py" % (self.zenpackdir, helper['component'].classname),
                           'text' : self.base_class % ( helper['component'].classname, 
                                                        helper['component'].classname,
                                                        self.indent )
                           })
        
        for v in helper['component'].classdata['infotext'].values(): self.info_text += v
                
        self.info_text += self.add_class % (helper['component'].helper.infoname, helper['component'].helper.infoname, self.indent)
        self.info_text += '\n'
        
        self.interfaces_text += self.add_class % (helper['component'].helper.interfacename, helper['component'].helper.interfacename, self.indent)
        self.interfaces_text += '\n'
        # datasource class
        if helper['datasource'] is not None:
            self.files.append({'name': "%s/datasources/%s.py" % (self.zenpackdir, helper['datasource'].classname),
                               'text' : self.base_class % (helper['datasource'].classname, 
                                                           helper['datasource'].classname,
                                                           self.indent)
                               })

            self.info_text += self.vocabulary_method % (self.zenpackname, helper['datasource'].classname, helper['component'].classname, helper['datasource'].classname)
            for v in helper['datasource'].classdata['infotext'].values(): self.info_text += v
            
            self.info_text += self.add_class % (helper['datasource'].helper.infoname, helper['datasource'].helper.infoname, self.indent)
            self.info_text += '\n'
            self.interfaces_text += self.add_class % (helper['datasource'].helper.interfacename, helper['datasource'].helper.interfacename, self.indent)
            self.interfaces_text += '\n'
        
    def buildFiles(self):
        ''' build the text that will comprise the zenpack'''
        
        self.info_text = self.construct_import        
        self.interfaces_text =  self.construct_import
        self.facades_text =  self.construct_import
        self.routers_text =  self.construct_import
        
        self.configure_xml = self.configure_start
        self.configure_xml += self.configure_zenpack % (self.zenpack.zenpackbase,
                                                        self.zenpack.helper.router_path,
                                                        self.zenpack.helper.adaptername,
                                                        self.zenpack.helper.ifacade_path,
                                                        self.zenpack.helper.facade_path,
                                                        self.zenpack.zenpackbase)
        
        # build the class files
        for k,v in self.helpers.items():  self.buildClassFiles(v)
        self.facades_text += self.add_class % (self.zenpack.helper.facadename, self.zenpack.helper.facadename, self.indent)
        self.facades_text += '\n'
        self.routers_text += self.add_class % (self.zenpack.helper.routername, self.zenpack.helper.routername, self.indent)
        self.routers_text += '\n'
        self.interfaces_text += self.add_class % (self.zenpack.helper.ifacadename, self.zenpack.helper.ifacadename, self.indent)
        self.interfaces_text += '\n'
        self.buildConfigureXML()
        self.configure_xml += self.configure_finish
        self.files.append({'name': "%s/configure.zcml" % self.zenpackdir, "text": self.configure_xml})
        self.buildJavaScriptFiles()
        self.files.append({ 'name': "%s/__init__.py" % self.zenpackdir, 'text': self.init_text })
        self.files.append({ 'name': "%s/info.py" % self.zenpackdir, 'text': self.info_text })
        self.files.append({ 'name': "%s/interfaces.py" % self.zenpackdir, 'text': self.interfaces_text })
        self.files.append({ 'name': "%s/facades.py" % self.zenpackdir, 'text': self.facades_text })
        self.files.append({ 'name': "%s/routers.py" % self.zenpackdir, 'text': self.routers_text })
        
    def buildConfigureXML(self):
        ''' basic configure.zcml file '''
        for k,v in self.helpers.items():
            comp = v['component']
            datasource = v['datasource']
            # add basic component checonfig
            self.configure_xml += self.configure_component % (comp.helper.info_path, 
                                                              comp.helper.class_path, comp.classname,
                                                              comp.helper.interface_path, 
                                                              comp.classname, comp.zenpackbase, comp.jsname)
            
            for line in comp.classdata['configure']:
                self.configure_xml += line
            # config js manual add UI support
            if comp.manual == True:
                self.configure_xml += self.configure_component_add % (comp.jsname, comp.zenpackbase, comp.jsname)
            # config for datasource 
            if datasource is not None:
                self.configure_xml += self.configure_datasource % (datasource.helper.info_path, 
                                                                   datasource.helper.class_path, datasource.classname,
                                                                   datasource.helper.interface_path,
                                                                   comp.classname, comp.classname, comp.classname)
                for line in datasource.classdata['configure']: self.configure_xml += line
    
    def buildJavaScriptFiles(self):
        ''' 
            build the component.js and component-add.js files
        '''
        for k,v in self.helpers.items():
            #log.debug( "building JS for %s" % k)
            construct = v['component']
            data = {
                    'name': "%s/resources/%s.js" % ( self.zenpackdir, construct.jsname),
                    'text' : self.js_display % ( construct.classname, construct.classname,
                                                 self.jsonify(self.jsonFields(construct.properties),16),
                                                 self.jsonify(self.jsonColumns(construct.properties),16),
                                                 construct.classname, construct.classname,
                                                 construct.classname, construct.classname,
                                                 construct.singular, construct.plural
                                                )
                    
                    }
            fix = ["Zenoss.render.severity", "Zenoss.render.locking_icons"]
            for f in fix:
                data['text'] = data['text'].replace('"%s"' % f, f)
            self.files.append(data)
            data = {
                    'name': "%s/resources/%s-add.js" % (self.zenpackdir, construct.jsname),
                    'text' : self.js_add % ( construct.singular, construct.singular,
                                             self.jsonAddFields(construct.properties),
                                             construct.zenpackbase, construct.helper.routername,
                                             construct.methods['router']['name'], construct.singular
                                            )
                    }
            
            #log.debug( "prepared %s" % data['name'])
            self.files.append(data)
    
    def build_skel(self):
        ''' 
            build the component.js and component-add.js files
        '''
        for d in self.zenpackdirectories:
            pathname = "%s/%s" % (self.zenpackdir,d)
            log.debug( "checking path: %s" % pathname)
            self.check_path(pathname)
            if d  not in ['resources','objects']:
                self.check_file("%s/__init__.py" % pathname)
                
    def clear_files(self):
        ''' 
            build the component.js and component-add.js files
        '''
        if 'ConstructionKit' in self.zenpackdir:  return
        ignoreDirs = ['modeler', 'modeler/plugins', 'objects', 'libexec', 'lib']
        for d in self.zenpackdirectories:
            if d in ignoreDirs: continue
            pathname = "%s/%s" % (self.zenpackdir,d)
            try:
                files = os.listdir(pathname)
                for f in files:
                    os.remove('%s/%s' % (pathname,f))
                os.remove(pathname)
            except:
                pass
                
    def check_path(self, path):
        ''' 
            create dir if it doesn't exist 
        '''
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
    
    def check_file(self, fname):
        ''' 
            create file if it doesn't exist
        '''
        if os.path.exists(fname):
            os.utime(fname, None)
        else:
            open(fname, 'w').close()
    
    def indentLines(self, lines, indent=5):
        ''' 
            write text to file
        '''
        #log.debug( "building file: %s with %s lines" % (filename,len(lines.split('\n'))) )
        newlines = ''''''
        for line in lines.split('\n'):
            newlines += """%s%s\n""" % (indent*' ', line)
        return newlines
    
    def writeLines(self, filename, lines, new=True):
        '''
            write text to file
        '''
        #log.debug( "building file: %s with %s lines" % (filename,len(lines.split('\n'))) )
        if new == True:
            cache = open(filename,'w')
        else:
            cache = open(filename,'a')
        for line in lines.split('\n'):
            cache.write("%s\n" % line)
        cache.close()
    
    def readLines(self, filename):
        '''
            read lines from file
        '''
        cache = open(filename,'r')
        return cache.read()
    
    def jsonify(self, data, spaces=4):
        ''''''
        return self.indentLines(json.dumps(data, indent=4),spaces)
    
    def jsonAddFields(self,data):
        '''
            format fields for the component-add.js file
        '''
        fields = []
        for v in data:
            if v.optional == False and v.isMethod == False:
                data = {
                        'xtype' : v.xtype(),
                        'name' : v.id,
                        'fieldLabel' : _t('%s') % v.title,
                        'id' : '%sField' % v.id,
                        'width' : 260,
                        'allowBlank' : v.is_optional()
                        }
                fields.append(data)
        cols = ['xtype', 'name', 'fieldLabel', 'id', 'width', 'allowBlank']
        #log.debug( "add fields: %s" % fields)
        output = self.jsonify(fields,24)
        for f in cols:
            output = output.replace('"%s"' % f, f)
        output = output.replace('"', "'")
        return output
    
    def jsonFields(self,data):
        '''
            fields for the component.js file
        '''
        fields = []
        for d in data:
            item = d.jsonComponentField()
            if item is not None:  fields.append(item)
        return self.js_add_start + fields + self.js_add_finish
    
    def jsonColumns(self,data):
        '''
            columns for the component.js file
        '''
        columns = []
        for v in data:
            item = v.jsonComponentColumn()
            if item is not None:  columns.append(item)
        return self.js_columns_start + columns + self.js_columns_finish

