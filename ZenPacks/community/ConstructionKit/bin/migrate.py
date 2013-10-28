#!/usr/bin/env python

import Globals
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
unused(Globals)

class Migrate(ZenScriptBase):
    """
    """
    
    def __init__(self, connect=True):
        ZenScriptBase.__init__(self, connect=True)
        """
        """
    def buildOptions(self):
        ZenScriptBase.buildOptions(self)
        self.parser.add_option("-w", "--write", dest="write", help="Write files", action="store_true")
  
    def run(self):
        """
                control script execution
        """
        # loop through and parse all Definition files, removing old options and making them compatible
        self.files = findDefinitionFiles(self.dmd)
        ignoreKeys = ['cycleTime','timeout', 'provided', 'eventClass']
        dsKeys = ['HttpComponent','NrpeComponent','SiebelComponent','SplunkSearch','TerracottaServer', 'TwillScript']
        for f in self.files:
            createDS = False
            newlines = ['from ZenPacks.community.ConstructionKit.BasicDefinition import *\n',
                        #'from ZenPacks.community.ConstructionKit.Construct import *'
                        ]
            
            lines = open(f,'r').readlines()
            for line in lines:
                for ds in dsKeys:
                    if ds in line:  createDS = True
                # make all classes subclasses of BasicDefinition
                if 'class' in line:  
                    newlines.append(line.replace('()','(BasicDefinition)'))
                else:
                    add = True
                    for k in ignoreKeys:
                        if k in line:  add = False
                    if add == True:
                        newlines.append(line)
            if createDS == True:  newlines.append('    createDS = True')
            # now write back to the Definition file
            print '            %s:' % f
            #for line in newlines:
            #    print line
            if self.options.write == True:
                print "writing changes to %s" % f
                newfile = open(f,'w')
                newfile.writelines(newlines)

if __name__ == "__main__":
    u = Migrate()
    u.run()


