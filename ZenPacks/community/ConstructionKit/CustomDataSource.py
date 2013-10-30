from Products.ZenModel.RRDDataSource import *
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from AccessControl import ClassSecurityInfo, Permissions
from Products.ZenUtils.ZenTales import talesCompile, getEngine
from Products.ZenUtils.Utils import binPath
import os

class CustomDataSource(ZenPackPersistence, RRDDataSource):
    ''''''
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
        if self.sourcetype == self.DATASOURCE:
            return self.component
        return RRDDataSource.getDescription(self)
    
    def useZenCommand(self):
        if self.cmdFile != None:
            return True
        return False
    
    def getData(self,data):
        '''change tuple of dictionary items to a single dictionary'''
        output = {}
        for d in data:
            output[d['id']] = d
        return output
    
    def getEventClasses(self):
        ''''''
        names = []
        for eventClass in self.getDmd().Events.getSubOrganizers():  
            name = eventClass.getOrganizerName()
            if name not in names:  names.append(name)
        return names
    
    def getCommand(ob, context, cmd=None):
        '''
            generate the plugin command
        '''
        if ob.cmdFile is not None: # this uses an external script
            cmd = binPath(ob.cmdFile)
            if ob.check_file(cmd) is False:  cmd = ob.cmdFile
            props = getattr(context,'_properties')
            data = ob.getData(props)
            parts = [cmd] + ob.evalArgs(context, data) + ob.addArgs(context, data)
            cmd = ' '.join(parts)
            cmd = RRDDataSource.getCommand(ob, context, cmd)
            return cmd
        else:
            if cmd is None:
                cmd = ob.commandTemplate
            if len(cmd) == 0:
                cmd = ob.command
            if not cmd.startswith('string:') and not cmd.startswith('python:'):
                cmd = 'string:%s' % cmd
            compiled = talesCompile(cmd)
            d = context.device()
            environ = {'dev' : d,
                       'device': d,
                       'devname': d.id,
                       'ds': ob,
                       'datasource': ob,
                       'here' : context,
                       'zCommandPath' : context.zCommandPath,
                       'nothing' : None,
                       'now' : DateTime() }
            res = compiled(getEngine().getContext(environ))
            if isinstance(res, Exception):
                raise res
            return res
    
    def getComponent(self, context, component=None):
        """Return localized component.
        """
        if component is None:
            component = self.component
        if not component.startswith('string:') and \
                not component.startswith('python:'):
            component = 'string:%s' % component
        compiled = talesCompile(component)
        d = context.device()
        environ = {'dev' : d,
                   'device': d,
                   'devname': d.id,
                   'here' : context,
                   'nothing' : None,
                   'now' : DateTime() }
        res = compiled(getEngine().getContext(environ))
        if isinstance(res, Exception):
            raise res
        self.getEventClass(environ, context.eventClass)
        return res
    
    def getEventClass(self, environ, eventClass=None):
        """Return localized eventClass.
        """
        if eventClass is None:
            eventClass = self.eventClass
        if not eventClass.startswith('string:') and \
                not eventClass.startswith('python:'):
            eventClass = 'string:%s' % eventClass
        compiled = talesCompile(eventClass)
        self.eventClass = compiled
        res = compiled(getEngine().getContext(environ))
        if isinstance(res, Exception):
            raise res
        self.eventClass = res
    
    def check_file(self, fname):
        ''' 
            create file if it doesn't exist
        '''
        if os.path.exists(fname):
            return True
        return False
        
    def evalArgs(self, context, data={}):
        ''' evaluate and return command line args '''
        parts = []
        for id,v in data.items():
            xtype = v['type']
            try:
                switch = v['switch']
            except:
                continue
            # check that property is relevant to the args
            if id in self.ignoreKeys: continue
            value = str(getattr(context, id))
            # check that value is popluated
            if value != "None" and len(str(value)) > 0:
                if xtype == 'string':# -x "XVAL"
                    parts.append('%s \"%s\"' % (switch, str(value)))
                elif xtype == 'lines': # -x "VAL1" "VAL2" "VAL3"...
                    parts.append('%s \"%s\"' % (switch, str(value)))
                elif xtype == 'list': # -x "VAL1" "VAL2" "VAL3"...
                    split_by_space = value.split(' ')
                    split_by_newline = value.split('\n')
                    values = split_by_newline
                    if len(split_by_space) > len(split_by_newline):
                        values = split_by_space
                    parts.append('%s \"%s\"' % (switch, '\" \"'.join(values)))
                elif xtype == 'boolean': # -x
                    if value == "True": parts.append(switch)
                else: # all other args
                    parts.append('%s %s' % (switch, value))
        return parts
    
    def addArgs(self, context, data):
        return []
    
    def checkCommandPrefix(self, context, cmd):
        if os.path.exists(self.getZenPack(context).path('libexec', self.cmdFile)):
            return self.getZenPack(context).path('libexec',cmd)
        return cmd
    
    def addDataPoints(self):
        for p in self.dpoints:
            if not self.datapoints._getOb(p, None):
                self.manage_addRRDDataPoint(p)
    
    def zmanage_editProperties(self, REQUEST=None):
        '''validation, etc'''
        if REQUEST:
            # ensure default datapoint didn't go away
            self.addDataPoints()
            # and eventClass
            #if not REQUEST.form.get('eventClass', None):
            #    REQUEST.form['eventClass'] = self.__class__.eventClass
        return RRDDataSource.zmanage_editProperties(self, REQUEST)
    
#    def onCollectorInstalled(self, event):
#        zpFriendly = self.component
#        errormsg = '{0} binary cannot be found on {1}. This is part of a ' + \
#                   'dependency, and must be installed before {2} can function.'
#        verifyBin = self.cmdFile
#        code, output = ob.executeCommand('zenbincheck ',verifyBin, 'zenoss', needsZenHome=True)
#        if code:
#            log.warn(errormsg.format(verifyBin, self.hostname, zpFriendly))
