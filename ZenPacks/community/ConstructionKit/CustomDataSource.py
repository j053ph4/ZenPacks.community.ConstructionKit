from Products.ZenModel.RRDDataSource import *
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from AccessControl import ClassSecurityInfo, Permissions
from Products.ZenUtils.ZenTales import talesCompile, getEngine
from Products.ZenUtils.Utils import binPath
import os

class CustomDataSource(ZenPackPersistence, RRDDataSource):
    '''Basic Class for ConstructionKit-based datasources'''
    DATASOURCE = ''
    sourcetype = DATASOURCE
    sourcetypes = (DATASOURCE,)
    dpoints = []
    cmdFile = None
    
    ignoreKeys = ['snmpindex','sourcetype', 'enabled', 
                  'component', 'eventComponent', 
                  'eventClass', 'eventKey',
                  'severity' 'commandTemplate',
                  'cycletime']
    
    def __init__(self, id, title=None, buildRelations=True):
        RRDDataSource.__init__(self, id, title, buildRelations)
        self.addDataPoints()
    
    def getDescription(self):
        '''return description of datasource'''
        if self.sourcetype == self.DATASOURCE: return self.component
        return RRDDataSource.getDescription(self)
    
    def useZenCommand(self):
        '''required'''
        if self.cmdFile: return True
        return False
    
    def getData(self,data):
        '''change tuple of dictionary items to a single dictionary'''
        output = {}
        for d in data: output[d['id']] = d
        return output
    
    def getEventClasses(self):
        '''return list of eventClasses'''
        names = []
        for eventClass in self.getDmd().Events.getSubOrganizers():  
            name = eventClass.getOrganizerName()
            if name not in names:  names.append(name)
        return names

    def getTALES(self, ob):
        '''return compiled TALES expression'''
        # make sure it is prepended with :string or :python for TALES
        if not ob.startswith('string:') and not ob.startswith('python:'):
            ob = 'string:%s' % ob
        return talesCompile(ob)
        
    def getComponent(self, context, component=None):
        ''' Return localized component. '''
        # choose default if not provided
        if component is None: component = self.component
        compiled = self.getTALES(component)
        d = context.device()
        environ = {
                   'dev' : d,
                   'device': d,
                   'devname': d.id,
                   'here' : context,
                   'nothing' : None,
                   'now' : DateTime() 
                   }
        res = compiled(getEngine().getContext(environ))
        if isinstance(res, Exception): raise res
        self.getEventClass(environ, context.eventClass)
        return res
    
    def getEventClass(self, environ, eventClass=None):
        '''Return localized (TALES-interpreted) eventClass.'''
        # choose default if not provided
        if eventClass is None: eventClass = self.eventClass
        compiled = self.getTALES(eventClass)
        self.eventClass = compiled
        res = compiled(getEngine().getContext(environ))
        if isinstance(res, Exception): raise res
        self.eventClass = res
    
    def check_file(self, fname):
        ''' create file if it doesn't exist '''
        if os.path.exists(fname): return True
        return False
    
    def getPropertyValue(self, context, prop_type, prop_id):
        ''''''
        value = getattr(context, prop_id, None)
        if value and prop_type == 'password':  return context.getPassword(prop_id)
        return value
    
    def getCommand(self, context, cmd=None):
        ''' generate the plugin command '''
        if self.cmdFile is not None: # this uses an external script
            cmd = binPath(self.cmdFile)
            if self.check_file(cmd) is False:  cmd = self.cmdFile
            props = getattr(context,'_properties')
            data = self.getData(props)
            parts = [cmd] + self.evalArgs(context, data) + self.addArgs(context, data)
            cmd = ' '.join(parts)
            cmd = RRDDataSource.getCommand(self, context, cmd)
            return cmd
        else:
            if cmd is None: cmd = self.commandTemplate
            if len(cmd) == 0: cmd = self.command
            compiled = self.getTALES(cmd)
            d = context.device()
            environ = {'dev' : d,
                       'device': d,
                       'devname': d.id,
                       'ds': self,
                       'datasource': self,
                       'here' : context,
                       'zCommandPath' : context.zCommandPath,
                       'nothing' : None,
                       'now' : DateTime() }
            res = compiled(getEngine().getContext(environ))
            if isinstance(res, Exception): raise res
            return res
    
    def evalArgs(self, context, data={}):
        ''' evaluate and return command line args '''
        parts = []
        arg = '''%s \"%s\"'''
        for prop_id, v in data.items():
            prop_type = v['type']
            flag = None
            # we only want properties that affect the command line arguments
            try: switch = v['switch']
            except: continue
            # check that property is relevant to the arguments
            if prop_id in self.ignoreKeys:  continue
            prop_value = self.getPropertyValue(context, prop_type, prop_id)
            if prop_value and len(str(prop_value)) > 0:
                # mostly we'll want quotes around the argument value
                if prop_type in ['string','password','lines']: 
                    flag = arg % (switch, prop_value)
                elif prop_type == 'list': # e.g -x "VAL1" "VAL2" "VAL3"...
                    split_by_space = prop_value.split(' ')
                    split_by_newline = prop_value.split('\n')
                    values = split_by_newline
                    # take whichever is greater in length
                    if len(split_by_space) > len(split_by_newline): 
                        values = split_by_space
                    flag = arg % (switch, '\" \"'.join(values))
                # for Boolean flags
                elif prop_type == 'boolean' and prop_value == True:  flag = switch 
                # don't quote any other args
                else: flag = '%s %s' % (switch, prop_value)
                # add to list of args
                if flag:  parts.append(flag)  
        return parts
    
    def addArgs(self, context, data):
        '''pass through for Definition-dependent monkeypatch'''
        return []
    
    def checkCommandPrefix(self, context, cmd):
        '''built-in to determine correct OS path'''
        if os.path.exists(self.getZenPack(context).path('libexec', self.cmdFile)):
            return self.getZenPack(context).path('libexec',cmd)
        return cmd
    
    def addDataPoints(self):
        '''built-in to return datapoints'''
        for p in self.dpoints:
            try:
                if not self.datapoints()._getOb(p, None):
                    self.manage_addRRDDataPoint(p)
            except:  pass
    
    def zmanage_editProperties(self, REQUEST=None):
        '''validation, etc'''
        # ensure default datapoint didn't go away
        if REQUEST: self.addDataPoints()
        return RRDDataSource.zmanage_editProperties(self, REQUEST)

