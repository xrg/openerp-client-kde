##############################################################################
#
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


import karamba

from Koo import Rpc
from PyQt4.QtGui import *

def initWidget(widget):
	global text
	global button
	text = karamba.createText( widget, 80, 35, 90, 30, status() )
	karamba.changeTextSize( widget, text, 16 )
	button = karamba.createImage( widget, 60, 90, "imgs/read-request.png" )
	karamba.attachClickArea( widget, button, "./launch-viewer.sh", "", "" )
	button = karamba.createImage( widget, 140, 90, "imgs/tinyerp-icon.ico" )
	karamba.attachClickArea( widget, button, "./launch-ktiny.sh", "", "" )

def widgetUpdated(widget):
	global text
	karamba.changeText( widget, text, status() )

def status():
	Rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'NaN' )
	ids, ids2 = Rpc.session.call( '/object', 'execute', 'res.request', 'request_get' )

	if len(ids) == 0:
		message = 'No requests'
	elif len(ids) == 1:
		message = 'One request'
	else:
		message = '%s requests' % len(ids)

	if len(ids2):
		message += '\n%s pending request(s)' % len(ids2)
	return message

