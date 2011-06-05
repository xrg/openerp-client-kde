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
from Koo.Screen.Screen import *
from Koo.Dialogs import FormWidget


def createScreenshots(model, id, ids, context):
	if not ids:
		return

	# Remove existing screenshots
	screenshot_ids = Rpc.session.execute('/object', 'execute', 'ir.documentation.screenshot', 'search', [('paragraph_id','in',ids),('user_id','=',Rpc.session.uid)])
	Rpc.session.execute('/object', 'execute', 'ir.documentation.screenshot', 'unlink', screenshot_ids)

	# Search views to be rendered
	view_ids = Rpc.session.execute('/object', 'execute', 'ir.documentation.view', 'search', [('paragraph_id','in',ids)])
	views = Rpc.session.execute('/object', 'execute', 'ir.documentation.view', 'read', view_ids, ['paragraph_id','reference','view_id','field'], context)

	for view in views:
		if not view['view_id']:
			continue

		reference = view['reference']
		paragraph_id = view['paragraph_id'][0]
		view_id = view['view_id'][0]
		field = view['field']

		record = Rpc.session.execute('/object', 'execute', 'ir.ui.view', 'read', [view_id], ['model','type'], context)[0]
		
		widget = FormWidget.FormWidget( record['model'], view_type=[ record['type'] ], view_ids=[view_id], context=context )
		if field:
			widget.screen.currentView().ensureFieldVisible( field )
		widget.setFixedSize( 800, 600 )
		widget.ensurePolished()
		widget.show()
		pixmap = QPixmap.grabWidget( widget )
		widget.hide()

		Rpc.session.execute('/object', 'execute', 'ir.documentation.screenshot', 'create', {
			'paragraph_id': paragraph_id,
			'view_id': view_id,
			'user_id': Rpc.session.uid,
			'reference': reference,
			'field': field,
			'image': base64.encodestring( pixmapToData( pixmap ) )
		}, context)

def pixmapToData(pixmap):
	if pixmap.isNull():
		return False
	bytes = QByteArray()
	buffer = QBuffer(bytes);
	buffer.open(QIODevice.WriteOnly);
	pixmap.save(buffer, "PNG")
	return str(bytes)

Plugins.register( 'screendocs', 'ir.documentation.paragraph', _('Create Screenshots'), createScreenshots)
