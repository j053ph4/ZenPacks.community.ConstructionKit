import logging
log = logging.getLogger('zen.migrate')

import Globals

from Products.ZenModel.ZenPack import ZenPackMigration
from Products.ZenModel.migrate.Migrate import Version
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *

unused(Globals)

class ConstructMigration(ZenPackMigration):

    version = '2.0.0'

    def migrate(self, dmd):
        log.info("Running ConstructMigration")

        # Do the migration work. No commit is needed.
        self.dmd = dmd

        log.info("saving custom components")
        c = Construct()
        for p in c.packs.keys():
            log.info("saving :%s" % p)
            for d in c.packs[p]['constructs'].keys():
                construct = c.packs[p]['constructs'][d]['component']
                saveDefinitionComponents(self.dmd, construct.classname)
                
        log.info("migrating Definition files")
        # loop through and parse all Definition files, removing old options and making them compatible
        self.files = findDefinitionFiles(self.dmd)
        ignoreKeys = ['cycleTime','timeout', 'provided', 'eventClass']
        for f in self.files:
            newlines = ['from ZenPacks.community.ConstructionKit.BasicDefinition import *\n',
                        #'from ZenPacks.community.ConstructionKit.Construct import *'
                        ]
            
            lines = open(f,'r').readlines()
            for line in lines:
                # make all classes subclasses of BasicDefinition
                if 'class' in line:  
                    newlines.append(line.replace('()','(BasicDefinition)'))
                else:
                    add = True
                    for k in ignoreKeys:
                        if k in line:  add = False
                    if add == True:
                        newlines.append(line)
            newfile = open(f,'w')
            newfile.writelines(newlines)
                
#        log.info("loading custom components")
#        c = Construct()
#        for p in c.packs.keys():
#            log.info("loading :%s" % p)
#            for d in c.packs[p]['constructs'].keys():
#                construct = c.packs[p]['constructs'][d]['component']
#                loadDefinitionComponents(self.dmd, construct.classname, construct.methods['add']['name'])


# Run the migration when this file is imported.
ConstructMigration()
