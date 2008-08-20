##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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

from PyQt4.QtCore  import *
from common import notifier
from common import options
import os
import base64
import tempfile

## @brief Provides various static functions to easily print files and/or data
# comming from the server.
#
# It encapsulates system dependent code and handles user preferences, such as
# sending directly to the printer if the system allows that.
class Printer(object):
	## @brief Opens the specified file with system's default application
	@staticmethod
	def open(fileName):
		if os.name == 'nt':
			os.startfile(fileName)
		else:
			os.spawnlp(os.P_NOWAIT, 'kfmclient', 'kfmclient', 'exec', fileName)
	
	## @brief Sends the specified file directly to the printer 
	@staticmethod
	def sendToPrinter(fileName):
		if os.name != 'nt':
			return
		import win32api
		win32api.ShellExecute (0, "print", fileName, None, ".", 0)
		
	## @brief Sends the specified file to printer or opens it with the default
	# application depending on operating system and user settings.
	@staticmethod
	def printFile(fileName, fileType):
		if os.name == 'nt' and options.options['printer.preview']:
			Printer.sendToPrinter( fileName )
		else:
			Printer.open( fileName )
	
	## @brief Prints report information contained in the data parameter. Which will 
	# typically be received from the server.
	@staticmethod
	def printData(data):
		if 'result' not in data:
			notifier.notifyWarning( _('Report error'), _('There was an error trying to create the report.') )
			return
			
		if data.get('code','normal')=='zlib':
			import zlib
			content = zlib.decompress(base64.decodestring(data['result']))
		else:
			content = base64.decodestring(data['result'])

		# We'll always try to open the file and won't limit ourselves to 
		# doc, html and pdf. For example, one might get odt, ods, etc. Before
		# we stored the report in a file if it wasn't one of the first three
		# formats.
		if data['format']=='html' and os.name=='nt':
			data['format']='doc'

		f = QTemporaryFile( 'XXXXXXXX.%s' % data['format'] )
		f.setAutoRemove( False )
		f.open()
		fileName = os.path.join( unicode( QDir.tempPath() ), unicode( f.fileName() ) )
		f.write( content )
		f.close()
		
		fp, fileName = tempfile.mkstemp( '.%s' % data['format'] )
		fp = os.fdopen( fp, 'wb+' )
		fp.write(content)
		fp.close()
		Printer.printFile( fileName, data['format'] )

