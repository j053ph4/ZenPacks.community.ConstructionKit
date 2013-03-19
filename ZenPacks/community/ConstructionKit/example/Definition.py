from ZenPacks.community.ConstructionKit.Construct import *
from Products.ZenModel.migrate.Migrate import Version
import os

class Definition():
    """
        Defines all data used within the ZenPack, including the new component class, its attributes, and data collection methods
    """
    # Version of this Zenpack
    version = Version(2, 0, 0)
    # first 2 parts of the Zenpack Name
    zenpackroot = "ZenPacks.community" # ZenPack Root
    # last part of the Zenpack Name
    zenpackbase = "zenHttpComponent" # ZenaPack Name
    # custom component class name
    component = 'HttpComponent'
    # dict of component properties
    componentData = {
                  # GUI listed (singular)
                  'singular': 'Monitored URL',
                  # GUI listed (plural)
                  'plural': 'Monitored URLs',
                  # display as component field in Event Console
                  'displayed': 'eventComponent',
                  # property used as primary key in class
                  'primaryKey': 'url',
                  # class attributes
                  'properties': { 
                        # Basic settings
                        #
                        #  addProperty arguments:
                        #        title: visible name in GUI
                        #        group: group for dialog elements
                        #        default:  any default value the property may have
                        #        switch:  command-line switch to pass data to nagios plugin (or other script)
                        #        optional:  whether this is a required property (default true)
                        #        override:  whether to set this property to default at component creation
                        #        isReference:  whether the default value is a literal value or a reference to a device property
                        #                         #
                        'hostname' : addProperty('Hostname (override)','Basic','id', switch='-H',override=True, isReference=True),
                        'ip' : addProperty('IP','Basic','manageIp', switch='-I',override=True, isReference=True),  
                        'port' : addProperty('Port','Basic','80', switch='-p',optional='false'),
                        'url' : addProperty('URL','Basic','/', switch='-u',optional='false'),
                        'ssl' : addProperty('SSL','Basic',False,'boolean', switch='-S',optional='false'),
                        # Authentication
                        'auth': addProperty('Authenticate','Authentication', False, ptype='boolean', switch='-a'),
                        'authUser' : addProperty('User','Authentication'),
                        'authPassword' : addProperty('Password','Authentication'),
                        'proxyAuth': addProperty('Proxy Authenticate','Authentication', False, ptype='boolean', switch='-b'),
                        'proxyAuthUser' : addProperty('Proxy User','Authentication'),
                        'proxyAuthPassword' : addProperty('Proxy Password','Authentication'),
                        # Content parsing
                        'regex' : addProperty('Regex (Case sensitive)','Content', switch='-r'),
                        'eregex' : addProperty('Regex (Case insensitive)','Content', switch='-R'),
                        'expect' : addProperty('Expect (comma-delimited strings)','Content', switch='-e'),
                        'string' : addProperty('Find string','Content', switch='-s'),
                        'invert' :  addProperty('Invert Match','Content',False, ptype='boolean', switch='--invert-regex'),
                        'post' : addProperty('POST','Content', switch='-P'),
                        'contentType' : addProperty('Content Type','Content', switch='-T'),
                        # Misc additional settings
                        'method': addProperty('HTTP method','Miscellaneous', switch='-j'),
                        'cert': addProperty('Certificate','Miscellaneous',False, ptype='boolean', switch='-C'),
                        'nobody': addProperty('Headers Only','Miscellaneous', False, ptype='boolean', switch='-N'),
                        'maxage' : addProperty('Max Age','Miscellaneous', switch='-M'),
                        'onRedirect' : addProperty('Redirect Behavior','Miscellaneous','follow', switch='-f'), 
                        # GUI Display Properties
                        'urlize' :  addProperty('Output Link','Display Settings',False,'boolean', switch='-L'),
                        'eventComponent' : addProperty('Alias','Display Settings','URL',optional='false'),
                        'eventKey' : addProperty('Event Key','Display Settings','/WWW'),
                        },
                  }
    # any new zProperties to be defined (same as usual format)
    packZProperties = []
    # name of the plugin or script to be used
    cmdFile = 'check_http'
    # whether this ZenPack provides the script
    provided = False
    # default check execution interval
    cycleTime = 300
    # default check timeout
    timeout = 60
    # default datapoints returned by the check
    datapoints = ['size','time']
    # ZenPack files directory (do not edit)
    cwd = os.path.dirname(os.path.realpath(__file__)) 
    
    
    
