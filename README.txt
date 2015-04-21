========================================
ZenPacks.community.ConstructionKit
========================================
TEST
About
=====

This ZenPacks automates to a large extent the development of other ZenPacks.  It eliminates the bulk of "boilerplate" code that 
accompanies the typical "custom component" type of zenpack while providing many nice features.  

The goal is to reduce the maintenance cost (development time) associated with dependent ZenPacks by removing most of their code.
ConstructionKit-dependent ZenPacks should consist only of a Definition.py class file that subclasses the provided "BasicDefinition" 
class, as well as any additional ZenPack-specific files such as modeler plugins, check scripts, and exported Zenoss templates, event 
classes, etc (objects.xml).


Requirements
============

Zenoss
------

You must first have, or install, Zenoss 4 or later. This ZenPack was tested against Zenoss 4.2.4.


Release Notes
=============

This version (2.0) is a major revision from version 1.0 and has been almost completely redesigned/rewritten.  It is much closer to my
originial design goals.  I ran into a major hurdle when designing the first version that directed me towards the use of "here docs" that 
is so present throughout its architecture.  I later learned that the problem i ran into was due to a bug in the initial Zenoss 4.x versions 
that has since been corrected.  While "here docs" are still in use, they are vastly simplified and used primarily as placeholders to guarantee 
correct python module loading paths.  They are also used to generate the javascript and configure.zcml files for dependent ZenPacks.  

The sheer number of changes may make upgrading difficult.  I have written and tested a few helper scripts to aid the proces, so please see the notes 
below before upgrading.  

Changes are far too numerous to list, but include:
	- much more dependent on class inheritance instead of per-ZenPack "here docs"
	- Inclusion of CustomComponent and CustomDatasource, the parent classes for dependent ZenPacks
	- Ability to specify additional parent classes for dependent zenpack (for property and relation inheritance)
	- Ability to add new class methods to subclassed components (via Definition.py)
	- Ability to add new class attributes to subclassed components (via Definition.py)
	- Ability to add new relations to subclassed components (via Definition.py)
	- new scripts to save/load custom components to/from a file (all or ZenPack-specific)
	- new script to rebuild all or specific dependent ZenPacks
	- migrate.py to rewrite old Definition.py classes to newer style (part of upgrade process)
	- install-zp.sh script to facilitate upgrade from ConstructionKit 1.0-based ZenPack to ConstructionKit 2.0-based ZenPack
	- many handy functions in ZenPackHelper class file to facilitate common development tasks

Installation
============

If no previous ConstructionKit version is installed, then install by the usual method.  Otherwise, please refer to the Upgrade section.
	

Upgrade
=======

As this is a major revision of ConstructionKit, some precautions should be taken prior to upgrading this ZenPack.  I recommend running a full backup
of the Zenoss installation prior to performing the upgrade.

First, in previous versions of the ConstructionKit, dependent ZenPacks are pretty close to being standalone in that the generated class files do not 
refer to the ConstructionKit at all.  In fact, if you remove any mention of the ConstructionKit modules, classes, methods, etc. in the __init__.py, 
then the derived ZenPack is effectively standalone.  We can take advantage of this fact when upgrading.

1)  To upgrade (from the command line), perform:

zenpack --install=ZenPacks.community.ConstructionKit-2.0.0-py2.7.egg ; zopectl restart ; zenhub restart 

CDIR="/opt/zenoss/ZenPacks/ZenPacks.community.ConstructionKit-2.0.0-py2.7.egg/ZenPacks/community/ConstructionKit"; # your path may differ
$CDIR/bin/save-components.py

The second step will create pickle files in /tmp that store any custom-created components from dependent ZenPacks.

Additionally, a helper function is included that can be run via zendmd to report the numbers and types of custom components.  
To run this check (in zendmd):

from ZenPacks.community.ConstructionKit.ZenPackHelper import *
countConstructs(dmd)

You should save this output to a text file for later reference.


2)  After upgrading the ZenPack, the Definition.py files (within dependent ZenPacks) should be updated to reflect the new style.  To do this, run:

$CDIR/bin/migrate.py -w ; zopectl restart ; zenhub restart 


3) After migrating the Definition.py files, new ZenPack files can be generated with:

$CDIR/bin/rebuild.py ; zopectl restart ;zenhub restart 


4) At this point it is a good idea to count the components again with:

from ZenPacks.community.ConstructionKit.ZenPackHelper import *
countConstructs(dmd)

and compare it to the previous results.


5) The upgrade is completed at this point.  Optionally (or if errors are noticed), run the following from zendmd:

from ZenPacks.community.ConstructionKit.ZenPackHelper import *
updateRelations(dmd, True)


6) Newer versions of dependent ZenPacks are forthcoming.  Installing these versions will likely delete existing instances of their custom
components, but included save/load scripts can be used to mitigate this damage.  

A script (install-zp.sh) has been included to automate this process, and should be used like:

CDIR="/opt/zenoss/ZenPacks/ZenPacks.community.ConstructionKit-2.0.0-py2.7.egg/ZenPacks/community/ConstructionKit"; # your path may differ
$CDIR/bin/install-zp.sh ZENPACKFILE.egg

This script will save the custom components to a file, run the zenpack installer, then reload the components from the file.


Developing with ConstructionKit
===============================


To create a ZenPack with a new custom component, perform the following:

1) Begin creating a ZenPack from the GUI in the usual fashion (as documented)
        a) be sure to set dependency on Zenpacks.community.ConstructionKit

2) From the command line:
        a) cd $ZENPACKHOME/ZENPACKS.NAME1.NAME2/ZENPACKS/NAME1/NAME2(replace with correct path to your Zenpack)
        b) rm -Rf *
        c) cp $ZENPACKHOME/ZenPacks.community.ConstructionKit/ZenPacks/community/ConstructionKit/example/* ./

3) Modify the "Definition.py" file as needed to suit needed component attributes and data collection methods

4) Reinstall the ZenPack from the command line with:
        zenpack --link --install=$ZENPACKHOME/ZENPACKS.NAME1.NAME2
        zopectl restart ; zenhub restart
        
5) Rebuild the Zenpack files with:

CDIR="/opt/zenoss/ZenPacks/ZenPacks.community.ConstructionKit-2.0.0-py2.7.egg/ZenPacks/community/ConstructionKit"; # your path may differ
$CDIR/bin/rebuild.py "ZENPACKS.NAME1.NAME2" ; zopectl restart ; zenhub restart
  
5) Manually copy any plugins/scripts you intend to distribute to:
        $ZENPACKHOME/ZENPACKS.NAME1.NAME2/ZENPACKS/NAME1/NAME2/libexec

6) Create any desired component-based RRD templates and add to the ZenPack

7) Zenpack can now be exported from Zenoss GUI and installed elsewhere (make sure the ConstructionKit dependency is set).


