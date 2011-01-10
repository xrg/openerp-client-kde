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
	printList( [x for x in gc.get_referrers( obj ) if not '<bound method ' in str(x)] )

def printList( l ):
	print '\n'.join( [str(x) for x in l] )

def info( text ):
	print text

def warning( text ):
	print text

def error( text ):
	print text

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
		

#
# Taken from py2exe's boot_common.py
#

import sys

if 'frozen' in dir(sys) and sys.frozen == "windows_exe":
	class Stderr(object):
		softspace = 0
		_file = None
		_error = None
		def write(self, text, alert=sys._MessageBox, fname=sys.executable + '.log'):
			if self._file is None and self._error is None:
				try:
					self._file = open(fname, 'a')
				except Exception, details:
					self._error = details
					import atexit
					atexit.register(alert, 0, "The logfile '%s' could not be opened:\n %s" % (fname, details), "Errors occurred")
				else:
					import atexit
					atexit.register(alert, 0, "See the logfile '%s' for details" % fname, "Errors occurred")
			if self._file is not None:
				self._file.write(text)
				self._file.flush()

		def flush(self):
			if self._file is not None:
				self._file.flush()
	sys.stderr = Stderr()
	del sys._MessageBox
	del Stderr

	class Blackhole(object):
		softspace = 0
		def write(self, text):
			pass
		def flush(self):
			pass
	sys.stdout = Blackhole()
	del Blackhole
	del sys

	# Disable linecache.getline() which is called by
	# traceback.extract_stack() when an exception occurs to try and read
	# the filenames embedded in the packaged python code.  This is really
	# annoying on windows when the d: or e: on our build box refers to
	# someone elses removable or network drive so the getline() call
	# causes it to ask them to insert a disk in that drive.
	import linecache
	def fake_getline(filename, lineno, module_globals=None):
		return ''
	linecache.orig_getline = linecache.getline
	linecache.getline = fake_getline

	del linecache, fake_getline


#app.installEventFilter( DebugEventFilter(win) )
