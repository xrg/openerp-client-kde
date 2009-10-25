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

## @brief The ArrowsEventFilter class provides an eventFilter that allows
# moving from one widget to another using Alt + Arrow (Left, Right, Up, Down) 
# and also Alt + Minus and Alt + Plus.
#
# To install it in an application use 'app.installEventFilter( Koo.Common.ArrowsEventFilter( mainWindow ) )'
class ArrowsEventFilter(QObject):
	## @brief Creates a new ArrowsEventFilter object.
	def __init__(self, parent=None):
		QObject.__init__(self, parent)

	# Get all visible and focusable child widgets of the given widget
	def allWidgets(self, object):
		if not object.isWidgetType():
			return []
		result = []
		if object.isVisible() and object.focusPolicy() != Qt.NoFocus and object.isEnabled():
			if object.inherits('QLineEdit'):
				if not object.isReadOnly():
					result += [ object ]
			else:
				result += [ object ]
		for child in object.children():
			result += self.allWidgets( child )
		return result

	def intersectVertically(self, rect1, rect2):
		if rect1.left() <= rect2.right() and rect1.right() >= rect2.left():
			return True
		return False

	def intersectHorizontally(self, rect1, rect2):
		if rect1.top() <= rect2.bottom() and rect1.bottom() >= rect2.top():
			return True
		return False
		
	def eventFilter(self, obj, event):
		if event.type() in (QEvent.KeyPress, QEvent.KeyRelease) and event.modifiers() & Qt.AltModifier and \
			event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Plus, Qt.Key_Minus): 

			if event.type() == QEvent.KeyRelease:
				return True

			mainWidget = QApplication.focusWidget()
			# Find parent window
			while not ( mainWidget.inherits( 'QDialog' ) or mainWidget.inherits( 'QMainWindow' ) ):
				mainWidget = mainWidget.parent()
				if not mainWidget:
					break

			if not mainWidget:
				return True

			currentWidget = QApplication.focusWidget()
			currentRect = currentWidget.rect()
			currentRect.moveTo( currentWidget.mapToGlobal( currentWidget.pos() ) )

			nextWidget = None
			nextArea = -1
			nextRect = None
			widgets = self.allWidgets(mainWidget)
			if currentWidget in widgets:
				widgets.remove( currentWidget )
			for widget in widgets:
				widgetRect = widget.rect()
				widgetRect.moveTo( widget.mapToGlobal( widget.pos() ) )
				widgetArea = widgetRect.width() * widgetRect.height()

				if event.key() == Qt.Key_Minus:
					if widgetRect.contains( currentRect ):
						if nextArea < 0 or widgetArea < nextArea:
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect
				elif event.key() == Qt.Key_Plus:
					if currentRect.contains( widgetRect ):
						if nextArea < 0 or widgetArea > nextArea:
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect
				elif event.key() == Qt.Key_Up:
					# Note that we check that both rects do NOT intersect. This means
					# that to browse to a widget container we must use Plus and Minus.
					# This makes speciall widgets such as QComboBox work properly.
					if self.intersectVertically( widgetRect, currentRect ) and \
						widgetRect.top() < currentRect.bottom() and \
						not widgetRect.intersects( currentRect ):
						
						if (not nextRect) or widgetRect.top() > nextRect.top():
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect
				elif event.key() == Qt.Key_Down:	
					# Note that we check that both rects do NOT intersect. This means
					# that to browse to a widget container we must use Plus and Minus.
					# This makes speciall widgets such as QComboBox work properly.
					if self.intersectVertically( widgetRect, currentRect ) and \
						widgetRect.bottom() > currentRect.top() and \
						not widgetRect.intersects( currentRect ):
						
						if (not nextRect) or widgetRect.bottom() < nextRect.bottom():
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect
				elif event.key() == Qt.Key_Left:
					if self.intersectHorizontally( widgetRect, currentRect ) and \
						widgetRect.right() < currentRect.left():
						
						if (not nextRect) or widgetRect.right() > nextRect.right():
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect
				elif event.key() == Qt.Key_Right:
					if self.intersectHorizontally( widgetRect, currentRect ) and \
						widgetRect.left() > currentRect.right():
						
						if (not nextRect) or widgetRect.left() < nextRect.left():
							nextWidget = widget
							nextArea = widgetArea
							nextRect = widgetRect

			if nextWidget:
				nextWidget.setFocus()
				return True
		return QObject.eventFilter( self, obj, event )	

