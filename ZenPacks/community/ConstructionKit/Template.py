from Products.Zuul.utils import ZuulMessageFactory as _t

class Template(object):
    '''
    container for "here docs" to construct various python objects
    '''
    INIT_TEXT = '''from ZenPacks.community.ConstructionKit.Construct import *
from ZenPacks.community.ConstructionKit.ZenPackConstruct import *
import Definition

init = Initializer(Definition)
for c in init.constructs: exec c.onCollectorInstalled()

class ZenPack(ZenPackConstruct):
    constructs = init.constructs
    packZProperties = init.props
    definitions = init.definitions
'''
    DEFINITION_SUBCLASS = '''from ZenPacks.community.ConstructionKit.BasicDefinition import *\nfrom ZenPacks.community.ConstructionKit.Construct import *\n\nDATA=%s\n\n%s = type('%s', (BasicDefinition,), DATA)\n'''

    CONSTRUCT_IMPORT = '''from ZenPacks.community.ConstructionKit.ClassHelper import *\n\n'''

    IMPORT_GLOBAL = """class %s(ClassHelper.%s):\n%s''''''\n"""

    BASE_CLASS = "%s%s" % (CONSTRUCT_IMPORT, IMPORT_GLOBAL)
    
    ADD_CLASS = IMPORT_GLOBAL

    COMPONENT_INTERFACE = '''from Products.Zuul.interfaces.component import IComponentInfo\nclass %s(IComponentInfo):\n    """"""\n\n'''
    
    DATASOURCE_INTERFACE = '''from Products.Zuul.interfaces import IRRDDataSourceInfo\nclass %s(IRRDDataSourceInfo):\n    """"""\n\n'''
    
    FACADE_CLASS = '''from Products.Zuul.interfaces import IFacade\nclass %s(IFacade):%s""""""\n\n'''
    
    ROUTER_CLASS = '''def _getFacade(self):\n%sfrom Products import Zuul\n%sreturn Zuul.getFacade('%s', self.context)\n\n'''
    
    ADDMETHOD='''
    from Products.ZenUtils.Utils import prepId
    from %s.%s import %s
    import re
    cid = '%s'
    for k,v in kwargs.iteritems():
        if type(v) != bool:
            cid += str(v)
    cid = re.sub('[^A-Za-z0-9]+', '_', cid)
    if len(cid) > 64 :
        cid = cid[:64]
    id = prepId(cid)
    component = %s(id)
    relation = target.%s.%s
    relation._setObject(component.id, component)
    component = relation._getOb(component.id)
    for k,v in kwargs.iteritems():
        setattr(component,k,v)\n%s
    component.updateCustomRelations()
    '''

    CREATEMETHOD = '''def %s(self, **kwargs):\n    target = self\n%s\n    return component\n'''

    FACADEMETHOD = '''def %s(self, ob, **kwargs):\n    """"""
    from Products.Zuul.utils import ZuulMessageFactory as _t
    target = ob\n%s\n    return True, _t("Added %s for device " + target.id)\n''' 
    
    IFACADEMETHOD = '''def %s(self, ob, **kwargs):\n   """"""\n'''

    ROUTERMETHOD = '''def %s(self, **kwargs):
    from Products.ZenUtils.Ext import DirectResponse
    facade = self._getFacade()
    ob = self.context
    success, message = facade.%s(ob, **kwargs)
    if success:  return DirectResponse.succeed(message)
    else: return DirectResponse.fail(message)\n'''
    
    ON_COLLECTOR_INSTALLED = '''def onCollectorInstalled%s(ob, event):
    zpFriendly = %s
    errormsg = '{0} binary cannot be found on {1}. This is part of a ' + \
               'dependency, and must be installed before {2} can function.'
    verifyBin = %s
    code, output = ob.executeCommand('zenbincheck ',verifyBin, 'zenoss', needsZenHome=True)
    if code:
        log.warn(errormsg.format(verifyBin, ob.hostname, zpFriendly))\n'''

    CONFIGURE_START='''<?xml version="1.0" encoding="utf-8"?>
    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:browser="http://namespaces.zope.org/browser"
        xmlns:zcml="http://namespaces.zope.org/zcml">
        <configure zcml:condition="installed Products.Zuul">

            <include package="Products.ZenUtils.extdirect.zope" file="meta.zcml"/>\n\n'''

    CONFIGURE_FINISH = '''\n        </configure>\n    </configure>\n'''

    CONFIGURE_ZENPACK = '''
            <!-- ZenPack Info -->

            <browser:directRouter
                name="%s_router"
                for="*"
                class="%s"
                namespace="Zenoss.remote"
                permission="zenoss.View"
            />
    
            <adapter
                name="%s"
                provides="%s"
                for="*"
                factory="%s"
            />
                
            <browser:resourceDirectory
                    name="%s"
                    directory="resources"
            />\n'''

    CONFIGURE_COMPONENT = '''
            <!-- Component Info -->
            <adapter factory="%s"
                for="%s.%s"
                provides="%s"
            />
    
            <browser:viewlet
                name="js-%s"
                paths="/++resource++%s/%s.js"
                weight="10"
                manager="Products.ZenUI3.browser.interfaces.IJavaScriptSrcManager"
                class="Products.ZenUI3.browser.javascript.JavaScriptSrcBundleViewlet"
                permission="zope2.Public"
            />\n'''

    CONFIGURE_COMPONENT_ADD = '''
            <browser:viewlet
                  name="component-add-menu-%s"
                  paths="/++resource++%s/%s-add.js"
                  weight="9"
                  for="Products.ZenModel.Device.Device"
                  manager="Products.ZenUI3.browser.interfaces.IHeadExtraManager"
                  class="Products.ZenUI3.browser.javascript.JavaScriptSrcBundleViewlet"
                  permission="zope2.Public"
            />\n'''

    CONFIGURE_DATASOURCE = '''
            <!-- Datasource Info -->
            <adapter factory="%s"
                for="%s.%s"
                provides="%s"
            />

            <utility provides="zope.schema.interfaces.IVocabularyFactory"
                component=".info.%sRedirectVocabulary"
                name="%sRedirectVocabulary"
            />

            <subscriber zcml:condition="installed ZenPacks.zenoss.DistributedCollector.interfaces"
                for="ZenPacks.zenoss.DistributedCollector.DistributedPerformanceConf.DistributedPerformanceConf
                     ZenPacks.zenoss.DistributedCollector.interfaces.ICollectorInstalled"
                handler=".onCollectorInstalled%s"
            />\n'''

    CONFIGURE_COMPONENT_VOLCABULARY = '''
            <utility provides="zope.schema.interfaces.IVocabularyFactory"
                component=".info.%s"
                name="%s"
            />\n'''
                
    COMPONENT_VOLCABULARY_METHOD = '''def %s(context):\n    return SimpleVocabulary.fromValues(context.%s())\n\n'''
        
    VOCABULARYMETHOD = '''from %s.datasources.%s import *\ndef %sRedirectVocabulary(context):\n    return SimpleVocabulary.fromValues(%s.onRedirectOptions)\n\n'''
 
    JS_DISPLAY='''\n(function(){
    var ZC = Ext.ns('Zenoss.component');

    function render_link(ob) {
        if (ob && ob.uid) {
            return Zenoss.render.link(ob.uid);
        } else {
            return ob;
        }
    }
    
    function pass_link(ob){ 
        return ob; 
    }
    
    ZC.%sPanel = Ext.extend(ZC.ComponentGridPanel, {
        constructor: function(config) {
            config = Ext.applyIf(config||{}, {
                componentType: '%s',
                autoExpandColumn: 'name', 
                fields: %s,
                columns:%s
            });
            ZC.%sPanel.superclass.constructor.call(this, config);
        }
    });
    
    Ext.reg('%sPanel', ZC.%sPanel);
    ZC.registerName('%s', _t('%s'), _t('%s'));
    
    })();\n'''

    JS_ADD = '''\n(function() {
        
            function getPageContext() {
                return Zenoss.env.device_uid || Zenoss.env.PARENT_CONTEXT;
            }
        
            Ext.ComponentMgr.onAvailable('component-add-menu', function(config) {
                var menuButton = Ext.getCmp('component-add-menu');
                menuButton.menuItems.push({
                    xtype: 'menuitem',
                    text: _t('Add %s') + '...',
                    hidden: Zenoss.Security.doesNotHavePermission('Manage Device'),
                    handler: function() {
                        var win = new Zenoss.dialog.CloseDialog({
                            width: 300,
                            title: _t('Add %s'),
                            items: [{
                                xtype: 'form',
                                buttonAlign: 'left',
                                monitorValid: true,
                                labelAlign: 'top',
                                footerStyle: 'padding-left: 0',
                                border: false,
                                items: %s
                                ,
                                buttons: [{
                                    xtype: 'DialogButton',
                                    id: '%s-submit',
                                    text: _t('Add'),
                                    formBind: true,
                                    handler: function(b) {
                                        var form = b.ownerCt.ownerCt.getForm();
                                        var opts = form.getFieldValues();
                                        Zenoss.remote.%s.%s(opts,
                                        function(response) {
                                            if (response.success) {
                                                new Zenoss.dialog.SimpleMessageDialog({
                                                    title: _t('%s Added'),
                                                    message: response.msg,
                                                    buttons: [{
                                                        xtype: 'DialogButton',
                                                        text: _t('OK'),
                                                        handler: function() { 
                                                            window.top.location.reload();
                                                            }
                                                        }]
                                                }).show();
                                            }
                                            else {
                                                new Zenoss.dialog.SimpleMessageDialog({
                                                    message: response.msg,
                                                    buttons: [{
                                                        xtype: 'DialogButton',
                                                        text: _t('OK'),
                                                        handler: function() { 
                                                            window.top.location.reload();
                                                            }
                                                        }]
                                                }).show();
                                            }
                                        });
                                    }
                                }, Zenoss.dialog.CANCEL]
                            }]
                        });
                        win.show();
                    }
                });
            });
        }()\n);\n'''
    
    JS_COLUMNS_START = [{'id': 'severity', 'dataIndex': 'severity', 'header': _t('Events'), 'renderer': "Zenoss.render.severity", 'sortable': 'true','width': 50},
                        {'id': 'name', 'dataIndex': 'name', 'header': _t('Name'), 'sortable': 'true', 'width': 70}]
    
    JS_COLUMNS_FINISH = [{'id': 'monitored', 'dataIndex': 'monitored', 'header': _t('Monitored'), 'sortable': 'true', 'width': 65},
                         {'id': 'locking', 'dataIndex': 'locking', 'header': _t('Locking'), 'renderer': "Zenoss.render.locking_icons", 'sortable':'true', 'width': 65}]
    
    JS_ADD_START = [{'name': 'uid'}, {'name': 'severity'}, {'name': 'status'}, {'name': 'name'}]

    JS_ADD_FINISH = [{'name': 'usesMonitorAttribute'}, {'name': 'monitor'}, {'name': 'monitored'}, {'name': 'locking'}]

