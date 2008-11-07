##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from Koo.Common import Common
from Koo.Common import Calendar
from Koo.View.AbstractView import *
import math

class GraphicsTaskItem( QGraphicsItemGroup ):
	# Parent should be a GraphicsDayItem
	def __init__(self, parent=None):
		QGraphicsItemGroup.__init__(self, parent)
		self._size = QSize(100, 100)
		self._text = QGraphicsTextItem( self )
		self._text.setTextWidth( self._size )
		self.addToGroup( self._text )

	def setSize(self, size):
		self._size = size
		self._text.setTextWidth( self._size )


class GraphicsDayItem( QGraphicsItemGroup ):
	def __init__(self, parent=None):
		QGraphicsItemGroup.__init__(self, parent)

		self._background = QGraphicsRectItem(self)
		self._background.setBrush( QBrush( QColor( 200, 200, 250) ) )
		self._background.setPen( QPen( QColor( 100, 100, 150) ) )
		self.addToGroup( self._background )

		self._title = QGraphicsTextItem(self)
		self._title.setPos( 0, 0 )
		self._title.setZValue( 1 )
		font = QFont()
		font.setBold( True )
		self._title.setFont( font )
		self.addToGroup( self._title )

		self._appointments = []

		self.setSize( QSize(100, 100) )
		self.setDate( QDate() )

	def setSize(self, size):
		self._size = size
		self._background.setRect( QRectF( 0, 0, self._size.width(), self._size.height() ) )
		self._title.setTextWidth( self._size.width() )

	def setDate(self, date):
		self._date = date
		self.updateData()

	def date(self):
		return self._date

	def addAppointment(self, id, title, message):
		self._appointments.append( { 'title': title, 'message': message } )
		self.updateData()
	
	def clearAppointments(self):
		self._appointments = []

	def updateData(self):
		apps = ''
		for x in self._appointments:
			apps += '<br/><b>%s</b><br/>%s' % ( x['title'], x['message'] )

		title = '<center>%s</center>' % ( unicode(self._date.toString()) )
		self._title.setHtml( title + apps )

class GraphicsCalendarItem( QGraphicsItemGroup ):
	def __init__(self, parent=None):
		QGraphicsItemGroup.__init__(self, parent)
		self._size = QSize( 100, 100 )
		self._multiRow = True
		self._itemsPerRow = 7
		self._startDate = QDate.currentDate()
		self._endDate = QDate.currentDate()
		self._days = {}
		self._model = None
		self._modelDateColumn = 0
		self._modelTitleColumn = 0

	def setSize( self, size ):
		self._size = size 
		self.updateCalendarView()

	def size(self):
		return self._size
	
	def setStartDate( self, date ):
		self._startDate = date
		self.updateCalendarView()

	def startDate(self):
		return self._startDate

	def setEndDate( self, date ):
		self._endDate = date
		self.updateCalendarView()

	def endDate(self):
		return self._endDate

	def daysCount(self):
		count = self._startDate.daysTo( self._endDate ) + 1
		if count < 0:
			return 0
		else:
			return count

	def updateCalendarView(self):
		self.clear()
		if not self.daysCount():
			return
		daysPerRow = 7
		offset = self._startDate.dayOfWeek() - 1
		rows = math.ceil( ( offset + self.daysCount() ) / 7.0 )
		if rows == 1:
			offset = 0
		dayWidth = self._size.width() / min( daysPerRow, self.daysCount() )
		dayHeight = self._size.height() / rows
		date = self._startDate
		for x in range( self._startDate.daysTo( self._endDate ) + 1 ):
			item = GraphicsDayItem( self )	
			item.setDate( date )
			item.setPos( (x+offset) % 7 * dayWidth, dayHeight * ( (x+offset) // 7 ) )
			item.setSize( QSize( dayWidth, dayHeight ) )
			self._days[ str(Calendar.dateToText( date )) ] = item
			date = date.addDays( 1 )
		self.updateCalendarData()

	def extractDate(self, variant):
		if not variant:
			return QDate()
		if variant.type() == QVariant.Date:
			return variant.toDate()
		elif variant.type() == QVariant.DateTime:
			return variant.toDateTime().date()
		else:
			return QDate()

	def updateCalendarData(self):
		if not self._model:
			return
		if self._modelDateColumn >= self._model.columnCount():
			return
		if self._modelTitleColumn >= self._model.columnCount():
			return

		for x in self._days.values():
			x.clearAppointments()

		for x in range(self._model.rowCount()):
			idx = self._model.index( x, self._modelDateColumn )
			date = str( self._model.data( idx ).toString() )
			date = date.split(' ')[0]
			if date in self._days:
				idx = self._model.index( x, self._modelTitleColumn )
				title = unicode( self._model.data( idx ).toString() )
				self._days[date].addAppointment( self._model.id(idx), title, '' )

	def clear(self):
		for item in self._days.keys():
			self._days[item].setParentItem( None )
			del self._days[item]
		self._days = {}

	def setModel(self, model):
		self._model = model
		self.updateCalendarData()

	def model(self):
		return self._model

	def setModelDateColumn(self, column):
		self._modelDateColumn = column
		self.updateCalendarData()

	def modelDateColumn(self):
		return self._modelDateColumn

	def setModelTitleColumn(self, column):
		self._modelTitleColumn = column
		self.updateCalendarData()

	def modelTitleColumn(self):
		return self._modelTitleColumn

class CalendarView( QGraphicsView ):
	def __init__(self, parent=None):
		QGraphicsView.__init__(self, parent)
		self._model = None
		self.setScene( QGraphicsScene(self) )
		self._calendar = GraphicsCalendarItem()
		self._calendar.setSize( self.size() )
		self.scene().addItem( self._calendar )

	def resizeEvent(self, event):
		self._calendar.setSize( QSize( self.size().width()-20, self.size().height()-20 ) )

	def setModel(self, model):
		self._calendar.setModel( model )

	def setModelDateColumn(self, column):
		self._calendar.setModelDateColumn( column )

	def setModelTitleColumn(self, column):
		self._calendar.setModelTitleColumn( column )

	def updateData(self):
		self._calendar.updateCalendarData()
		self._calendar.updateCalendarView()

(ViewCalendarUi, ViewCalendarBase) = loadUiType( Common.uiPath('calendarview.ui') )

class ViewCalendar( AbstractView, ViewCalendarUi ):
	def __init__(self, parent):
		AbstractView.__init__(self, parent)
		ViewCalendarUi.__init__(self)
		self.setupUi( self )
		self.connect( self.calendarWidget, SIGNAL('selectionChanged()'), self.updateCalendarView )
		self.connect( self.pushMonthlyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.connect( self.pushWeeklyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.connect( self.pushDailyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.setReadOnly( True )
		self.title = ""
		self.view_type = 'calendar'
		self.updateCalendarView()

	def setModel(self, model):
		self.calendarView.setModel( model )

	def setModelDateColumn(self, column):
		self.calendarView.setModelDateColumn( column )

	def setModelTitleColumn(self, column):
		self.calendarView.setModelTitleColumn( column )

	def updateCalendarView(self):
		date = self.calendarWidget.selectedDate()
		if self.pushMonthlyView.isChecked():
			start = QDate( date.year(), date.month(), 1 )
			end = QDate( date.year(), date.month(), date.daysInMonth() )
		elif self.pushWeeklyView.isChecked():
			start = date.addDays( 1 - date.dayOfWeek() )
			end = date.addDays( 7 - date.dayOfWeek() )
		else:
			start = date
			end = date
		self.calendarView._calendar.setStartDate( start )
		self.calendarView._calendar.setEndDate( end )

	def display(self, currentModel, models):
		self.calendarView.updateData()

