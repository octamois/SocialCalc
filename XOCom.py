import threading
from threading import *
from logic import ServerLogic
from server import Server
from instance import Instance
from sugar.activity.activity import get_bundle_path
from hulahop.webview import WebView
from xpcom import components
from localized_strings_file import localized_strings

class XOCom:
    # Constructor gives full XPCom access by default
    # This should be improved for future apps that may not need/want full access
    cometPort = 8889
    ajaxPort = 8890

    def __init__(self, control_sending_text,uri=None):
        self.cond = Condition()
        #h = hash(Instance.instanceId)
        self.__class__.cometPort = 10
        self.__class__.ajaxPort = 11
        self.cometLogic = ServerLogic(self)
        #self.ajaxServer = ServerThread(self.__class__.ajaxPort, self.cometLogic)
        #self.ajaxServer.start()
        #self.cometServer = ServerThread(self.__class__.cometPort, self.cometLogic)
        #self.cometServer.start()
        if uri:
            self.uri = uri
        else:
            self.uri = 'file://' + get_bundle_path() + '/web/index.html?ajax='+str(self.__class__.ajaxPort)+'&comet='+str(self.__class__.cometPort);
        self.control_sending_text=control_sending_text
        self.give_full_xpcom_access()
        self.set_observer()
        ##self.send_to_browser_localize(['initlocalize'])  ## to initialize the localized strings in socialcalc
	
    # Give the browser permission to use XPCom interfaces
    # This is necessary for XPCom communication to work
    # Note: Not all of these preferences may be required - requires further
    #       investigation
    def give_full_xpcom_access(self):
        pref_class = components.classes["@mozilla.org/preferences-service;1"]
        prefs = pref_class.getService(components.interfaces.nsIPrefService)
        prefs.getBranch('signed.applets.').setBoolPref('codebase_principal_support',
                True);
        prefs.getBranch('capability.principal.').setCharPref(
                        'socialcalc.granted', 'UniversalXPConnect')
        prefs.getBranch('capability.principal.').setCharPref(
                        'socialcalc.id', self.uri)

    # Wrapper method to create a new webview embedded browser component
    # Uses hulahop's WebView.  Assumes that you'll want to serve
    # web/index.html relative to your activity directory.
    def create_webview(self):
        self.web_view = WebView()
        ##self.uri = 'file://' + get_bundle_path() + '/web/index.html';
        self.web_view.load_uri(self.uri)
        self.web_view.show()
        return self.web_view
    
    def set_observer(self):
        #try:
            print 'enter: set_observer'
            observerService = components.classes["@mozilla.org/observer-service;1"]
            ob_serv = observerService.getService(components.interfaces.nsIObserverService);
            observer=Observer(self.control_sending_text)
            ob_serv.addObserver(observer,"xo-message2",False);
            print 'exit: set_observer'
        #except:
            #print 'error is there, remove try and except thing'
        
        
    # Use XPCom to execute a javascript callback registered with XO.js
    # The command will execute a javascript method registered with the same name,
    # and return any value received from the javascript
    def send_to_browser(self, command, parameter=None):
        if((command == "read") and (parameter is not None)):
            self.web_view.load_uri("javascript:XO.observer.setSheet('"+parameter.replace('\\n','DECNEWLINE').replace('\n','NEWLINE').replace("'","\\'")+"');void(0);")
            return

        # Set up an array for parameters and return values for the XPCom call
        array = components.classes["@mozilla.org/array;1"].createInstance(
                components.interfaces.nsIMutableArray)
     
        # Optionally pass data to the javascript
        if parameter: 
            str = components.classes["@mozilla.org/supports-string;1"].createInstance(
                        components.interfaces.nsISupportsString)
            str.data = parameter
            array.appendElement(str, False)

        # Use XPCom to send an event to a javascript observer (web/xo.js)
        observerService = components.classes["@mozilla.org/observer-service;1"]
        ob_serv = observerService.getService(components.interfaces.nsIObserverService)
        ob_serv.notifyObservers(array, "xo-message", command)
        #ob_serv.addObserver(self.control_sending_text,"xo-message2",False)

        # check if the browser returned anything
        if array.length:
            iter = array.enumerate()
            result = iter.getNext()
            result = result.QueryInterface(components.interfaces.nsISupportsString)
            return result.toString()
        return None
    
    def send_to_browser_shared(self,command):
        if command[0]=='execute':
            array = components.classes["@mozilla.org/array;1"].createInstance(components.interfaces.nsIMutableArray)
            str = components.classes["@mozilla.org/supports-string;1"].createInstance(components.interfaces.nsISupportsString)
            str.data = command[1]
            array.appendElement(str, False)
            str2 = components.classes["@mozilla.org/supports-string;1"].createInstance(components.interfaces.nsISupportsString)
            str2.data = command[2]
            array.appendElement(str2, False)
            
            observerService = components.classes["@mozilla.org/observer-service;1"]
            ob_serv = observerService.getService(components.interfaces.nsIObserverService);
            if not array.length: 
                print 'no need of sending anywhere , array is empty'
            ob_serv.notifyObservers(array, "xo-message", 'execute');

    def send_to_browser_localize(self,command):
        #self.ajaxServer.closing = 1
        print 'sending to javascript part to localize\n'
        #array = components.classes["@mozilla.org/array;1"].createInstance(components.interfaces.nsIMutableArray)
        localstr = "javascript:XO.lang=["
        for i,j in localized_strings.iteritems():
            localstr = localstr+"'"+i.replace("'","\\'")+"','"+j.replace("'","\\'")+"',"
            #str1 = components.classes["@mozilla.org/supports-string;1"].createInstance(components.interfaces.nsISupportsString)
            #str1.data=i
            #array.appendElement(str1, False)
            #str2 = components.classes["@mozilla.org/supports-string;1"].createInstance(components.interfaces.nsISupportsString)
            #str2.data=j
            #array.appendElement(str2, False)
        localstr = localstr+"'xv'];XO.observe();void(0);"
        self.web_view.load_uri(localstr)
        return

        observerService = components.classes["@mozilla.org/observer-service;1"]
        ob_serv = observerService.getService(components.interfaces.nsIObserverService);
        if not array.length: 
           print 'no need of sending anywhere , array is empty'
        ob_serv.notifyObservers(array, "xo-message3", 'initlocalize');

        if array.length:
            iter = array.enumerate()
            result = iter.getNext()
            result = result.QueryInterface(components.interfaces.nsISupportsString)
            print result.toString()
        
    
class Observer():
    _com_interfaces_ = components.interfaces.nsIObserver
    def __init__(self,control_sending_text):

        print 'just initiating'
        self.control_sending_text=control_sending_text
        self.content_observe=''
    def observe(self, service, topic, extra):
        print 'getting the signal in the python part'
        
        
            
        if topic=="xo-message2":   #it is for the execute command type'
            service = service.QueryInterface(components.interfaces.nsIMutableArray)
            if service.length:
                iter = service.enumerate()
                result = iter.getNext()
                result = result.QueryInterface(components.interfaces.nsISupportsString)
                self.content_observe=result.toString()
                print 'the content in observer of xocom is ', self.content_observe
                saveundostring=iter.getNext()
                saveundostring=saveundostring.QueryInterface(components.interfaces.nsISupportsString)
                saveundostring=saveundostring.toString()
                sendingArray=['execute',self.content_observe,saveundostring]
                self.control_sending_text(array=sendingArray,str='execute')
        

class ServerThread(threading.Thread):
    def __init__(self,port,logic):
        threading.Thread.__init__(self)
        self.startserver(port,logic)

    def startserver(self,port,logic):
        try:
            self.server = Server(("127.0.0.1",port),logic)
            self.closing = 0
        except:
            self.startserver(port+2,logic)

    def run(self):
        try:
            self.server.serve_forever()
        except:
            if(self.closing == 0):
                self.run()

    def stop(self):
        r = 2
