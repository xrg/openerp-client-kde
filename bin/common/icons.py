from PyQt4.QtGui import *

#
# GTK -> KDE Icons mapping
# Due to the fact that the server expects the client to understand GTK icon names
# we used a set of two functions and a dictionary to help us work correctly.
# The 'mapIcons' dictionary should have an entry for each icon name used by 
# the server, the value of the entry is the name of the image in our resource
# file. Simply use kdeIcon() and kdePixmap() functions to get the appropiate 
# Icon or Pixmap.
mapIcons = {
	'gtk-ok' : 'ok.png',
	'gtk-cancel' : 'cancel.png',
	'gtk-go-forward' : 'next.png',
	'gtk-go-back' : 'previous.png',
	'gtk-info' : 'info.png',
	'gtk-close' : 'close.png',
	'gtk-dialog-info' : 'info.png',
	'STOCK_JUSTIFY_FILL' : 'text_block.png',
	'STOCK_INDENT' : 'rightjust.png',
	'STOCK_OPEN' : 'folder.png',
	'STOCK_EXECUTE' : 'action.png',
	'STOCK_NEW' : 'new.png',
	'STOCK_PREFERENCES' : 'configure.png',
	'STOCK_CONVERT' : 'convert.png',
	'terp-graph' : 'chart.png',
	'terp-partner' : 'partner.png',
	'terp-account' : 'account.png',
	'terp-hr' : 'hr.png',
	'terp-product' : 'product.png',
	'terp-graph' : 'chart.png',
	'terp-stock' : 'stock.png',
	'terp-crm' : 'crm.png',
	'terp-purchase' : 'purchase.png',
	'terp-mrp' : 'mrp.png',
	'terp-sale' : 'sale.png',
	'terp-administration' : 'administration.png',
	'terp-project': 'clock.png'
}

## @brief Returns a QIcon given an icon name. The name of the icon is usually a 
# GTK or TinyERP name.
def kdeIcon(icon):
	if icon in mapIcons:
		return QIcon( ':/images/images/' + mapIcons[icon] )
	else:
		print "KDE ICON '%s' NOT FOUND" % icon
		return QIcon()

## @brief Returns a QPixmap given an icon name. The name of the icon is usually 
# a GTK or TinyERP name.
def kdePixmap(icon):
	if icon in mapIcons:
		return QPixmap( ':/images/images/' + mapIcons[icon] )
	else:
		print "KDE ICON '%s' NOT FOUND" % icon
		return QPixmap()

