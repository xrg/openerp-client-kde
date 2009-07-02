#   Copyright (C) 2009 by Albert Cervera i Areny
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

## @brief The AbstactKeyboardWidget provides an abstract class for creating virtual
# on-screen keyboards.
class AbstractKeyboardWidget(QWidget):
	## @brief Creates a KeyboardWidget that will send keyboard events to it's parent. It will
	# also be positioned in the screen acording to its parent coordinates.
	def __init__(self, parent):
		QWidget.__init__(self, parent)

	# @brief Initializes keyboard by connecting buttons to slots. Setting window flags. And 
	# positioning it in the screen.
	def init(self):
		self.connect( self.pushEscape, SIGNAL('clicked()'), self.escape )
		if hasattr(self, 'pushCaps'):
			self.connect( self.pushCaps, SIGNAL('clicked()'), self.caps )
		else:
			self.pushCaps = None
		buttons = self.findChildren( QPushButton )
		for button in buttons:
			if button in (self.pushCaps, self.pushEscape):
				continue
			self.connect( button, SIGNAL('clicked()'), self.clicked )

		self.setWindowFlags( Qt.Popup )
		self.setWindowModality( Qt.ApplicationModal )
		self.setFocusPolicy( Qt.NoFocus )
		all = self.findChildren( QWidget )
		for widget in all:
			widget.setFocusPolicy( Qt.NoFocus )
		self.fitInScreen()
		if self.pushCaps:
			self.caps()
		self.show()

	## @brief Tries to position the Keyboard in the best place in the screen.
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
		# We expect objectName to be filled with the appropiate name Qt gives
		# to the Key the button should emulate.
		key = self.key( unicode( button.objectName() ) )
		if not key:
			print 'No key assigned to button "%s"' % unicode( button.text() )
			return
		event = QKeyEvent( QEvent.KeyPress, key, Qt.NoModifier, button.text() )
		QApplication.sendEvent( self.parent(), event )
	
	## @brief Returns the value of "Qt.Key_" + text value.
	def key(self, text):
		return eval( 'Qt.%s' % text )

	## @brief Hides the keyboard.
	def escape(self):
		self.hide()

	def caps(self):
		buttons = self.findChildren( QPushButton )
		for button in buttons:
			if button.text().count() == 1:
				if self.pushCaps.isChecked():
					button.setText( button.text().toUpper() )
				else:
					button.setText( button.text().toLower() )

