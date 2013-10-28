#!/usr/bin/env python
import Globals
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
from Products.ZenUtils.ZenScriptBase import ZenScriptBase
from optparse import OptionParser
unused(Globals)

class SaveComponents(ZenScriptBase):
    """
    """
    def __init__(self):
        """
        """
        ZenScriptBase.__init__(self, connect=True)

    def run(self):
        """
                control script execution
        """
        c = Construct()
        if self.options.zenpack is not "all":
            print "saving component info for: %s" % self.options.zenpack
            for d in c.packs[self.options.zenpack]['constructs'].keys():
                construct = c.packs[self.options.zenpack]['constructs'][d]['component']
                saveDefinitionComponents(self.dmd, construct.classname)
        else:
            for p in c.packs.keys():
                print "saving component info for: %s" % p
                for d in c.packs[p]['constructs'].keys():
                    construct = c.packs[p]['constructs'][d]['component']
                    saveDefinitionComponents(self.dmd, construct.classname)
    
    def buildOptions(self):
        ZenScriptBase.buildOptions(self)
        self.parser.add_option("-Z", dest="zenpack", help="Zenpack Name (default all)", default="all")

if __name__ == "__main__":
    u = SaveComponents()
    u.run()


