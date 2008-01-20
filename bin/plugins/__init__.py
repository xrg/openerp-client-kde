from PyQt4.QtGui import *
from common import common
import re
import os

# This function obtains the list of all available plugins by iterating
# over every subdirectory inside plugins/
def listPlugins():
	# Search for all available plugins
	plugs = {}
	dir=os.path.abspath(os.path.dirname(__file__))
	for i in os.listdir(dir):
		path = os.path.join( dir, i, '__terp__.py' )
		if os.path.isfile( path ):
			try:
				x = eval(file(path).read())
				# Store the module we need to import in order
				# to execute the 'action'
				
				for y in x:
					x[y]['module'] = i
				plugs.update( x )
			except:
				print "Error importing view: ", i
	return plugs
	

# Shows the plugin selection dialog and executes the one selected
def execute(datas):
	result = {}
	plugins = listPlugins()
	print plugins
	for p in plugins:
		if not 'model_re' in plugins[p]:
			plugins[p]['model_re'] = re.compile(plugins[p]['model'])
		res = plugins[p]['model_re'].search(datas['model'])
		if res:
			result[plugins[p]['string']] = p
	if not len(result):
		QMessageBox.information(None, '',_('No available plugin for this resource !'))
		return 
	sel = common.selection(_('Choose a Plugin'), result, alwaysask=True)
	if sel:
		# Import the appropiate module and execute the action
		exec('import %s' % plugins[sel[1]]['module'])
		exec('%s(%s)' % ( plugins[sel[1]]['action'], datas ) )
