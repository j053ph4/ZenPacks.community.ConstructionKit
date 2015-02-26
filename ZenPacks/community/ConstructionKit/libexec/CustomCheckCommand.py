#!/usr/bin/env python
import sys, os, re
import Globals
from optparse import OptionParser
from Products.ZenUtils.ZenScriptBase import ZenScriptBase

class CustomCheckCommand(ZenScriptBase):
    """
    """
    def __init__(self, connect=False):
        ZenScriptBase.__init__(self)
        if connect is True:  self.connect()
        self.status = 0
        self.message = ''
        self.exitStatusMap = {'OK': 0, 'WARNING' : 1, 'CRITICAL' : 2}

    def buildOptions(self):
        ''''''
        ZenScriptBase.buildOptions(self)
    
    def run(self):
        ''''''
        self.initialize()
        self.evalStatus()
        self.finished()
        
    def initialize(self):
        ''''''
        pass

    def evalStatus(self):
        ''''''
        pass
    
    def finished(self):
        ''''''
        print self.message
        sys.exit(self.status) 
        
    def startWatch(self):
        '''start the clock'''
        self.start = time.time()
    
    def stopWatch(self, message):
        '''check run time of script'''
        end = time.time() - self.start
        if self.verbose  is True:  print '%s in %0.1f s' % (message, end)
        self.start = time.time()
    
if __name__ == "__main__":
    u = CustomCheckCommand()
    u.run()
