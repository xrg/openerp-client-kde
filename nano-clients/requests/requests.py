import karamba

import rpc
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
	rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'graficas' )
	ids, ids2 = rpc.session.call( '/object', 'execute', 'res.request', 'request_get' )

	if len(ids) == 0:
		message = 'No requests'
	elif len(ids) == 1:
		message = 'One request'
	else:
		message = '%s requests' % len(ids)

	if len(ids2):
		message += '\n%s pending request(s)' % len(ids2)
	return message

