#!/usr/bin/env python

import Globals
from Products.ZenUtils.Utils import unused
unused(Globals)
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
from Products.ZenUtils.ZenScriptBase import ZenScriptBase

class Rebuild(ZenScriptBase):
    """
    """
    def __init__(self, connect=True):
        """
        """
        ZenScriptBase.__init__(self, connect=True)

    def buildOptions(self):
        ZenScriptBase.buildOptions(self)
        self.parser.add_option("-Z", dest="zenpack", help="Zenpack Name (default all)", default="all")

    def run(self):
        """
                control script execution
        """
        c = Construct()
        if self.options.zenpack is not "all":
            print "rebuilding %s" % self.options.zenpack
            c.zenpackname = self.options.zenpack
            c.buildZenPackFiles()
        else:
            c.rebuild()
        #print "rebuilding relations"
        #updateRelations(self.dmd,True)

if __name__ == "__main__":
    u = Rebuild()
    u.run()


