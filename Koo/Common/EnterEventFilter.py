#   Copyright (C) 2009 by Albert Cervera i Areny  albert@nan-tic.com
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

## @brief The EnterEventFilter class provides an eventFilter that treats
# Enter key events as if they were Tab Key hits. Exceptions are buttons 
# (in which it's replaced with space) and QTextEdits in which it's the event
# is sent as is.
#
# To install it in an application use 'app.installEventFilter( Koo.Common.EnterEventFilter( mainWindow ) )'
class EnterEventFilter(QObject):
	## @brief Creates a new EnterEventFilter object.
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	## @brief Reimplements eventFilter() to send the Tab Key press
	def eventFilter(self, obj, event):
		if event.type() in (QEvent.KeyPress, QEvent.KeyRelease) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
			if isinstance(obj, QPushButton) or isinstance(obj, QToolButton):
				event = QKeyEvent( event.type(), Qt.Key_Space, event.modifiers(), event.text(), event.isAutoRepeat(), event.count() )
				QApplication.sendEvent( obj, event )
				return True
			elif type(obj) in (QLineEdit, QComboBox, QCheckBox):
				if obj.parent() and obj.parent().inherits( 'AbstractFieldWidget' ):
					event = QKeyEvent( event.type(), Qt.Key_Tab, event.modifiers(), event.text(), event.isAutoRepeat(), event.count() )
					QApplication.sendEvent( obj, event )
					return True
		return QObject.eventFilter( self, obj, event )	

