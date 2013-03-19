========================================
ZenPacks.community.ConstructionKit
========================================

About
=====

This ZenPack seeks to automate many typical tasks associated with custom component Zenpack development.  It provides a set of
template files (basically "here documents") that are used to generate all of the various python files used by other ZenPacks.

Dependent Zenpacks need only 2 files: an "__init__.py" (copied from the "example" directory) and a "Definiton.py" (copied and 
modified from the "example" directory).  The Definition.py file defines all of the custom component attributes, etc, as well as any
scripts that will be used to collect the data.

Requirements
============

Zenoss
------

You must first have, or install, Zenoss 3 or later. This ZenPack was tested
against Zenoss 3.2 and Zenoss 4.2.0.


Installation
============

Install ZenPack on server
--------------------------------

Download the `Distributed Collectors ZenPack <http://community.zenoss.org/docs/DOC-5861>`_.
Copy this file to your Zenoss server and run the following commands as the zenoss
user.

    ::

        zenpack --install ZenPacks.community.ConstructionKit-1.0.egg
        zenoss restart


Usage
=====

ZenPack Development
-------------------

To create a ZenPack with a new custom component, perform the following:

1) Begin creating a ZenPack from the GUI in the usual fashion (as documented)
	a) be sure to set dependency on Zenpacks.community.ConstructionKit
	
2) From the command line:
	a) cd $ZENPACKHOME/ZENPACKS.NAME1.NAME2/ZENPACKS/NAME1/NAME2(replace with correct path to your Zenpack)
	b) rm -Rf *
	c) cp $ZENPACKHOME/ZenPacks.community.ConstructionKit/ZenPacks/community/ConstructionKit/example/* ./

3) Modify the "Definiton.py" file as needed to suit needed component attributes and data collection methods

4) Reinstall the ZenPack from the command line with:
	zenpack --link --install=$ZENPACKHOME/ZENPACKS.NAME1.NAME2/ZENPACKS/NAME1/NAME2
	zopectl restart ; zenhub restart
	
5) Manually copy any plugins/scripts you intend to distribute to:
	$ZENPACKHOME/ZENPACKS.NAME1.NAME2/ZENPACKS/NAME1/NAME2/libexec
	
6) Create any desired component-based RRD templates and add to the ZenPack
	
7) Zenpack can now be exported from Zenoss GUI and installed elsewhere (make sure the ConstructionKit dependency is met).


