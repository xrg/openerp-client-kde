##############################################################################
#
# Copyright (c) 2008-2010 NaN Projectes de Programari Lliure, S.L. All rights reserved
#                         http://www.NaN-tic.com
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

import base64
from Koo import Rpc
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from Common.Ui import *
from Koo.Plugins import Plugins

try:
	from NanScan.Scanner import *
	from NanScan.ScanDialog import *
	isNanScanAvailable = True
except:
	isNanScanAvailable = False
	

if isNanScanAvailable:
	def scan(model, id, ids, context):
		saver = DocumentSaverFactory(context)
		dialog = ScanDialog()
		dialog.setImageSaverFactory( saver )
		dialog.exec_()

	class DocumentSaverFactory(AbstractImageSaverFactory):
		def __init__(self, context):
			self.context = context

		def create(self, parent):
			saver = DocumentSaver( parent )
			saver.context = self.context
			return saver

	class DocumentSaver(AbstractImageSaver):
		def run(self):
			self.error = True

			image = QBuffer()
			if not self.item.image.save( image, 'PNG' ):
				return
	
			id = Rpc.session.execute('/object', 'execute', 'nan.document', 'create', {
				'name': unicode( self.item.name ),
				'datas': base64.encodestring( str(image.buffer()) ),
				'filename': _('document.png'),
			}, self.context )
			if not id:
				return

			self.error = False

	Plugins.register( 'scanner', 'nan.document', _('Scan Documents'), scan )
