##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

# ------------------------------------------------------------------- #
# Module printer
# ------------------------------------------------------------------- #
#
# Supported formats: pdf
#
# Print or open a previewer
#

from PyQt4.QtGui import *
from common import notifier
from common import options
import os, base64
import gc

class Printer(object):

	def __init__(self):
		self.openers = {
			'pdf': self._findPDFOpener,
			'html': self._findHTMLOpener,
			'doc': self._findHTMLOpener,
		}

	def _findHTMLOpener(self):
		if os.name == 'nt':
			return lambda fileName: os.startfile(fileName)
		else:
			return lambda fileName: QDesktopServices.openUrl( fileName )

	def _findPDFOpener(self):
		if os.name == 'nt':
			if options.options['printer.preview']:
				return lambda fn: os.startfile(fn)
			else:
				return lambda fn: print_w32_filename(fn)
		else:
			return lambda fileName: os.spawnlp(os.P_NOWAIT, 'kfmclient', 'kfmclient', 'exec', fileName)

	def print_file(self, fname, ftype):
		finderfunc = self.openers[ftype]
		opener = finderfunc()
		opener(fname)
		gc.collect()

printer = Printer()

def print_w32_filename(filename):
	import win32api
	win32api.ShellExecute (0, "print", filename, None, ".", 0)

def print_data(data):
	if 'result' not in data:
		notifier.notifyWarning( _('Report error'), _('There was an error trying to create the report.') )
		return
		
	if data.get('code','normal')=='zlib':
		import zlib
		content = zlib.decompress(base64.decodestring(data['result']))
	else:
		content = base64.decodestring(data['result'])

	if data['format'] in printer.openers.keys():
		import tempfile
		if data['format']=='html' and os.name=='nt':
			data['format']='doc'
		fp_name = tempfile.mktemp('.'+data['format'])
		fp = file(fp_name, 'wb+')
		fp.write(content)
		fp.close()
		printer.print_file(fp_name, data['format'])
	else:
		fname = QFileDialog.getOpenFileName(None, _('Write Report to File'), os.path.join(options.options['client.default_path'], data['format']) )
		try:
			fp = file(filename,'wb+')
			fp.write(content)
			fp.close()
		except:
			QMessageBox.information(None, '', _('Error writing the file!'))

