##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All rights reserved
#                    http://www.NaN-tic.com
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
# as published by the Free Software Foundation; either version 3
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

import os
import base64
from Koo import Rpc
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *
from Koo.Plugins import Plugins
from Koo.Common import Calendar

def scan(model, id, ids, context):
	Directories = 1
	Files = 0
	Cancel = 2
	dialog = QMessageBox()
	dialog.setWindowTitle( _('Import Documents') )
	dialog.setText( _('How do you want to import documents?') )
	dialog.addButton( _('Select Files'), 3 )
	dialog.addButton( _('Selected Directory'), 2 )
	dialog.addButton( _('Cancel Import'), 1 )
	result = dialog.exec_()
	if result == Cancel:
		return

	if result == Directories:
		directory = unicode( QFileDialog.getExistingDirectory() )
		if not directory:
			return
		fileNames = QDir( directory ).entryList()
		fileNames = [os.path.join( directory, unicode(x) ) for x in fileNames]
	else:
		fileNames = QFileDialog.getOpenFileNames()
		fileNames = [unicode(x) for x in fileNames]
			
			
	for fileName in fileNames:
		try:
			# As fileName may not be a file, simply try the next file.
			f = open(fileName, 'rb')
		except:
			continue
		try:
			data = base64.encodestring( f.read() )
		except:
			continue
		finally:
			f.close()
		id = Rpc.session.execute('/object', 'execute', 'nan.document', 'create', {
			'name': Calendar.dateTimeToText( QDateTime.currentDateTime() ),
			'datas': data,
			'filename': os.path.basename(fileName),
		}, context )

Plugins.register( 'document-importer', 'nan.document', _('Import Documents'), scan )
