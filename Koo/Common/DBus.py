import Debug

try:
	import dbus.mainloop.qt
	import dbus.service
	import dbus
	isDBusAvailable = True
except:
	isDBusAvailable = False
	Debug.info( _("Module 'dbus' not available. Consider installing it so other applications can easily interact with Koo.") )

if isDBusAvailable:
	# The OpenErpInterface gives access from DBUS to local api.
	# To test it you may simply use the following command line: 
	# qdbus org.openerp.Interface /OpenERP org.openerp.Interface.call "createWindow" "None, 'res.partner', False, [], 'form', mode='form,tree'"
	#
	class OpenErpInterface(dbus.service.Object):
		def __init__(self, path):
			dbus.service.Object.__init__(self, dbus.SessionBus(), path)

		# This function lets execute any given function of the KooApi. See example above.
		@dbus.service.method(dbus_interface='org.openerp.Interface', in_signature='sss', out_signature='')
		def call(self, serviceName, function, parameters):
			f = 'Api.instance.%s(%s)' % (function, parameters) 
			eval(f)

def init():
	if not isDBusAvailable:
		return
	dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
	sessionBus = dbus.SessionBus()
	name = dbus.service.BusName("org.openerp.Interface", sessionBus )
	example = OpenErpInterface('/OpenERP')

