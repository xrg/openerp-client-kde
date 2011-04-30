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
	'gtk-apply' : 'apply.png',
	'gtk-cancel' : 'cancel.png',
	'gtk-close' : 'close.png',
	'gtk-convert' : 'convert.png',
	'gtk-dialog-info' : 'info.png',
	'gtk-execute' : 'exec.png',
	'gtk-find' : 'find.png',
	'gtk-go-back' : 'previous.png',
	'gtk-go-down' : 'down.png',
	'gtk-go-forward' : 'next.png',
	'gtk-go-up' : 'up.png',
	'gtk-indent': 'indent.png',
	'gtk-info' : 'info.png',
	'gtk-jump-to' : 'relate.png',
	'gtk-media-next' : 'media_next.png',
	'gtk-media-pause' : 'pause.png',
	'gtk-media-previous' : 'media_previous.png',
	'gtk-ok' : 'ok.png',
	'gtk-open' : 'open.png',
	'gtk-print' : 'print.png',
	'gtk-save' : 'save.png',
	'gtk-select-all' : 'text_block.png',
	'gtk-undo' : 'undo.png',
	'STOCK_CONVERT' : 'convert.png',
	'STOCK_EXECUTE' : 'action.png',
	'STOCK_INDENT' : 'rightjust.png',
	'STOCK_JUSTIFY_FILL' : 'text_block.png',
	'STOCK_NEW' : 'new.png',
	'STOCK_OPEN' : 'folder.png',
	'STOCK_PREFERENCES' : 'configure.png',
	'STOCK_PRINT' : 'print.png',
	'STOCK_SELECT_COLOR' : 'colorpicker.png',
	'STOCK_PRINT_PREVIEW' : 'print.png',
	'terp-administration' : 'administration.png',
	'terp-account' : 'account.png',
	'terp-calendar': 'calendar.png',
	'terp-crm' : 'crm.png',
	'terp-dialog-close': 'close.png',
	'terp-document-new' : 'new.png',
	'terp-graph' : 'chart.png',
	'terp-gtk-go-back-rtl' : 'reload.png',
	'terp-gtk-jump-to-ltr' : 'next.png',
	'terp-hr' : 'hr.png',
	'terp-mrp' : 'mrp.png',
	'terp-partner' : 'partner.png',
	'terp-personal' : 'partner.png',
	'terp-product' : 'product.png',
	'terp-project': 'clock.png',
	'terp-accessories-archiver' : 'product.png',
	'terp-purchase' : 'purchase.png',
	'terp-sale' : 'sale.png',
	'terp-stock' : 'stock.png',
	'terp-stock_effects-object-colorize': 'view_tree.png',
	'reload': 'reload.png'
}

## @brief Returns a QIcon given an icon name. The name of the icon is usually a 
# GTK or OpenERP name.
def kdeIcon(icon):
	if icon in mapIcons:
		return QIcon( ':/images/' + mapIcons[icon] )
	else:
		if icon:
			print "KDE ICON '%s' NOT FOUND" % icon
		return QIcon()

## @brief Returns a QPixmap given an icon name. The name of the icon is usually 
# a GTK or OpenERP name.
def kdePixmap(icon):
	if icon in mapIcons:
		return QPixmap( ':/images/' + mapIcons[icon] )
	else:
		if icon:
			print "KDE ICON '%s' NOT FOUND" % icon
		return QPixmap()

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
