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
	'gtk-media-previous' : 'media_previous.png',
	'gtk-media-next' : 'media_next.png',
	'gtk-print' : 'print.png',
	'gtk-apply' : 'apply.png',
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
	'terp-project': 'clock.png',
	'terp-calendar': 'calendar.png',
	'reload': 'reload.png'
}

## @brief Returns a QIcon given an icon name. The name of the icon is usually a 
# GTK or OpenERP name.
def kdeIcon(icon):
	if icon in mapIcons:
		return QIcon( ':/images/images/' + mapIcons[icon] )
	else:
		print "KDE ICON '%s' NOT FOUND" % icon
		return QIcon()

## @brief Returns a QPixmap given an icon name. The name of the icon is usually 
# a GTK or OpenERP name.
def kdePixmap(icon):
	if icon in mapIcons:
		return QPixmap( ':/images/images/' + mapIcons[icon] )
	else:
		print "KDE ICON '%s' NOT FOUND" % icon
		return QPixmap()

