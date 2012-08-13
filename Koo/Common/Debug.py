##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import gc
from PyQt4.QtCore import *

def printObjects():
	printList( gc.get_objects() )

def printReferrers( obj ):
	printList( [str(x) for x in gc.get_referrers( obj ) if not '<bound method ' in str(x)] )

def printList( l ):
	print '\n'.join( [str(x) for x in l] )

def info( text ):
	try:
		print str(text)
	except:
		print "Error trying to print info message."

def warning( text ):
	try:
		print str(text)
	except:
		print "Error trying to print warning message."

def error( text ):
	try:
		print str(text)
	except:
		print "Error trying to print error message."

# The DebugEventFilter class has been used to find a problem with an invisible
# widget that was created, not inserted in any layout and that didn't allow to 
# click widgets below it. I'm leaving the code by now as it might be useful in the
# future. Simply uncommenting the installEventFilter line will do.
class DebugEventFilter(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		
	def eventFilter(self, obj, event):
		print "EVENT %d THROWN ON OBJECT '%s' OF TYPE '%s'" % ( event.type(), unicode(obj.objectName() ), unicode(obj.staticMetaObject.className()) )
		return QObject.eventFilter( self, obj, event )
		
#app.installEventFilter( DebugEventFilter(win) )

#
# Taken from py2exe's boot_common.py
#

import sys

if 'frozen' in dir(sys) and sys.frozen == "windows_exe":
	now = QDateTime.currentDateTime()
	now = str( now.toString( Qt.ISODate ) )
	fname = sys.executable + '.log'
	try:
		sys.stderr = open(fname, 'a')
		sys.stderr.write( '--- %s ---\n' % now )
	except:
		warning( 'Error opening file: %s' % fname )

	class Blackhole(object):
		softspace = 0
		def write(self, text):
			pass
		def flush(self):
			pass
	sys.stdout = Blackhole()

def exceptionHook(type, value, backtrace):
	from PyQt4.QtGui import QApplication
	cursor = QApplication.overrideCursor()
	if cursor:
		QApplication.restoreOverrideCursor()
	from Settings import Settings
	import traceback
	backtrace = ''.join( traceback.format_tb( backtrace ) )
	if Settings.value('client.debug'):
		from Koo.Common import Notifier
		Notifier.notifyError( type, value, backtrace )
	else:
		error( 'Error: %s\n%s\n%s' % (type, value, backtrace) )

def installExceptionHook():
	sys.excepthook = exceptionHook

def debug_trace():
	'''Set a tracepoint in the Python debugger that works with Qt.  
	Removes "QCoreApplication::exec: The event loop is already running" messages while in pdb'''
	from PyQt4.QtCore import pyqtRemoveInputHook
	from pdb import set_trace
	pyqtRemoveInputHook()
	set_trace()

