#   Copyright (C) 2008 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or 
#   (at your option) any later version. 
#
#   This program is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License 
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from Koo.Common import Common

(KeypadWidgetUi, KeypadWidgetBase) = loadUiType( Common.uiPath('keypad.ui') )

class KeypadWidget(QWidget, KeypadWidgetUi):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		KeypadWidgetUi.__init__( self )
		self.setupUi( self )

		self.connect( self.pushEscape, SIGNAL('clicked()'), self.escape )
		buttons = self.findChildren( QPushButton )
		for button in buttons:
			if button == self.pushEscape:
				continue
			self.connect( button, SIGNAL('clicked()'), self.clicked )

		self.setWindowFlags( Qt.Popup )
		self.setWindowModality( Qt.ApplicationModal )
		self.setFocusPolicy( Qt.NoFocus )
		all = self.findChildren( QWidget )
		for widget in all:
			widget.setFocusPolicy( Qt.NoFocus )
		self.fitInScreen()
		self.show()

	def attachTo(self, widget):
		self._widget = widget
		self.fitInScreen()
		self.show()

	def fitInScreen(self):
		parent = self.parent()
		parentPos = parent.parent().mapToGlobal( parent.pos() )
		screenHeight = QApplication.desktop().screenGeometry().height()
		screenWidth = QApplication.desktop().screenGeometry().width()
		# Fix y coordinate
		y = parentPos.y() + parent.height()
		if y + self.height() > screenHeight:
			y = parentPos.y() - self.height()
			if y < 0:
				y = screeHeight - self.height()
		# Fix x coordinate
		x = parentPos.x() + parent.width() / 2 - self.width() / 2
		if x < 0:
			x = 0
		elif x + self.width() > screenWidth:
			x = screenWidth - self.width()
		self.move( x, y )

	def clicked(self):
		button = self.sender()
		key = self.key( unicode( button.objectName() ) )
		if not key:
			print 'No key assigned to button "%s"' % unicode( button.text() )
			return
		event = QKeyEvent( QEvent.KeyPress, key, Qt.NoModifier, button.text() )
		QApplication.sendEvent( self.parent(), event )

	def key(self, text):
		return eval( 'Qt.%s' % text )

	def escape(self):
		self.hide()

