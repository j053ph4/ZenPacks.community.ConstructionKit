#!/usr/bin/env python
import sys, os, re
import Globals
from optparse import OptionParser
from Products.ZenUtils.ZenScriptBase import ZenScriptBase

class CustomCheckCommand(ZenScriptBase):
    """
    """
    def __init__(self):
        ZenScriptBase.__init__(self, connect=False)
        self.status = 0
        self.message = ''

    def buildOptions(self):
        """
        """
        ZenScriptBase.buildOptions(self)
    
    def run(self):
        """
        """
        self.initialize()
        self.evalStatus()
        self.finished()
        
    def initialize(self):
        """
        """
        pass

    def evalStatus(self):
        """
        """
        pass
    
    def finished(self):
        """
        """
        print self.message
        sys.exit(self.status) 
 
if __name__ == "__main__":
    u = CustomCheckCommand()
    u.run()
