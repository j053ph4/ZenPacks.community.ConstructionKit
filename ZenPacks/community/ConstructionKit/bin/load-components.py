#!/usr/bin/env python

import Globals
from Products.ZenUtils.Utils import unused
from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
from Products.ZenUtils.ZenScriptBase import ZenScriptBase

from optparse import OptionParser
unused(Globals)


class LoadComponents(ZenScriptBase):
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
            for d in c.packs[self.options.zenpack]['constructs'].keys():
                construct = c.packs[self.options.zenpack]['constructs'][d]['component']
                loadDefinitionComponents(self.dmd, construct.classname, construct.methods['add']['name'])
        else:
            for p in c.packs.keys():
                for d in c.packs[p]['constructs'].keys():
                    construct = c.packs[p]['constructs'][d]['component']
                    loadDefinitionComponents(self.dmd, construct.classname, construct.methods['add']['name'])

    def buildOptions(self):
        ZenScriptBase.buildOptions(self)
        self.parser.add_option("-Z", dest="zenpack", help="Zenpack Name (default all)", default="all")

if __name__ == "__main__":
    u = LoadComponents()
    u.run()


