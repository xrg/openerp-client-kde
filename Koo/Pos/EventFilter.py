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
from KeyboardWidget import *
from KeypadWidget import *

## @brief The PosEventFilter class provides an eventFilter that shows a Keyboard for touchscreen 
# environemnts when a QLineEdit or QTextEdit gets the focus (is clicked by the user).
#
# In order to enable the Keyboard (and Keypad) in an application, simply install
# it with 'app.installEventFilter( Koo.Pos.PosEventFilter( mainWindow ) )'
class PosEventFilter(QObject):
	## @brief Creates a new PosEventFilter object.
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.currentWidget = None
		self.keyboard = None

	## @brief Reimplements eventFilter() to show a Keyboard when a QLineEdit or QTextEdit gets
	# the focus.
	def eventFilter(self, obj, event):
		if event.type() == QEvent.MouseButtonPress:
			if obj != self.currentWidget:
				if obj.inherits( 'QLineEdit' ) or obj.inherits( 'QTextEdit' ):
					self.currentWidget = obj
					self.openKeyboard( obj )
		elif event.type() == QEvent.FocusOut:
			if obj and obj == self.currentWidget and self.keyboard:
				self.keyboard.hide()
				self.keyboard = None
				self.currentWidget = None
		return QObject.eventFilter( self, obj, event )

	def tabKeyPressed(self):
		widget = QApplication.focusWidget()
		if widget and ( widget.inherits( 'QLineEdit' ) or widget.inherits( 'QTextEdit' ) ):
			self.openKeyboard( widget )
		else:
			self.closeKeyboard()

	def openKeyboard(self, obj):
		self.closeKeyboard()
		if obj.parent() and ( obj.parent().inherits( 'FloatFieldWidget' ) or obj.parent().inherits( 'IntegerFieldWidget' ) ): 
			self.keyboard = KeypadWidget( obj )
		else:
			self.keyboard = KeyboardWidget( obj )
		self.connect( self.keyboard, SIGNAL( 'tabKeyPressed' ), self.tabKeyPressed )

	def closeKeyboard(self):
		if self.keyboard:
			try:
				self.keyboard.setParent(None)
				del self.keyboard
			except:
				pass
			self.keyboard = None

