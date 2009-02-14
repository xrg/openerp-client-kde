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
from Keyboard import *
from Keypad import *

class PosEventFilter(QObject):
	def __init__(self, parent=None):
		QObject.__init__(self, parent)
		self.currentWidget = None
		self.keyboard = None

	def eventFilter(self, obj, event):
		if event.type() == QEvent.FocusIn:
			if obj != self.currentWidget:
				if obj.inherits( 'QLineEdit' ) or obj.inherits( 'QTextEdit' ):
					self.currentWidget = obj
					if self.keyboard:
						try:
							self.keyboard.setParent(None)
							del self.keyboard
						except:
							pass
						self.keyboard = None

					if obj.parent() and ( obj.parent().inherits( 'FloatFieldWidget' ) or obj.parent().inherits( 'IntegerFieldWidget' ) ): 
						self.keyboard = KeypadWidget( obj )
					else:
						self.keyboard = KeyboardWidget( obj )

		elif event.type() == QEvent.FocusOut:
			if obj and obj == self.currentWidget and self.keyboard:
				self.keyboard = None
				self.currentWidget = None
		return QObject.eventFilter( self, obj, event )

