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
		self._background = QGraphicsRectItem( self )
		self._background.setBrush( QBrush( QColor( 200, 250, 200 ) ) )
		self._background.setPen( QPen( QColor( 100, 200, 100 ) ) )
		self._text = QGraphicsTextItem( self )
		self._text.setZValue( 1 )
		self.setSize( QSize(100, 100) )
		self.addToGroup( self._text )
		self._index = None

	def setSize(self, size):
		self._size = size
		self._text.setTextWidth( self._size.width() )
		self._background.setRect( 0, 0, size.width(), size.height() )

	def setTitle(self, title):
		self._title = title
		self._text.setPlainText( title )

	def setIndex(self, index):
		self._index = index

	def index(self):
		return self._index

class Appointment:
	def __init__(self):
		self.start = QDateTime()
		self.end = QDateTime()
		self.id = None
		self.title = ''
		self.message = ''

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

		#self._appointments = []
		self._indexes = {}
		self._tasks = {}

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

	def addModelIndex(self, index):
		if index in self._tasks.keys():
			return
		task = GraphicsTaskItem( self )
		task.setZValue( 1 )
		task.setIndex( index )
		self.addToGroup( task )
		self._indexes[ task ] = index
		self._tasks[ index ] = task
		self.updateData()

	def removeModelIndex(self, index):
		if not index in self._tasks.keys():
			return
		task = self._tasks[ index ]
		self.removeFromGroup( task )
		del self._tasks[ index ]
		del self._indexes[ task ]
		self.updateData()

	def clear(self):
		self._indexes = {}
		self._tasks = {}

	def updateData(self):
		#apps = ''
		#for x in self._appointments:
			#apps += '<br/><b>%s</b><br/>%s' % ( x['title'], x['message'] )
#
		title = '<center>%s</center>' % ( unicode(self._date.toString()) )
		self._title.setHtml( title )
		for index in self._tasks.keys():
			task = self._tasks[index] 
			model = index.model()
			titleIdx = model.index( index.row(), self.parentItem()._modelTitleColumn )
			dateIdx = model.index( index.row(), self.parentItem()._modelDateColumn )
			task.setTitle( titleIdx.data().toString() )

			startTime = self.parentItem().dateTimeFromIndex( dateIdx ).time()
			secs = QTime( 0, 0 ).secsTo( startTime )
			height = self._size.height()
			y = QTime( 0, 0 ).secsTo( startTime ) * self._size.height() / 86400.0
			task.setPos( 0, y )
			task.setSize( QSize( self._size.width(), 50 ) )

			title = unicode( titleIdx.data().toString() )


class GraphicsCalendarItem( QGraphicsItemGroup ):

	ValueRole = Qt.UserRole + 1

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
			x.clear()

		for x in range(self._model.rowCount()):
			idx = self._model.index( x, self._modelDateColumn )
			date = Calendar.dateToText( self.dateTimeFromIndex( idx ).date() )
			if date in self._days:
				idx = self._model.index( x, self._modelTitleColumn )
				#title = unicode( self._model.data( idx ).toString() )
				self._days[date].addModelIndex( idx )

	def dateTimeFromIndex(self, idx):
		data = self._model.data( idx )
		if data.type() == QVariant.DateTime:
			return data.toDateTime()
		data = self._model.data( idx, self.ValueRole )
		if data.type() == QVariant.DateTime:
			return data.toDateTime()
		# If neither DisplayRole nor ValueRole contain
		# a DateTime, simply return an invalid DateTime object
		return QDateTime()
		
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

class GraphicsCalendarScene( QGraphicsScene ):
	def __init__(self, parent=None):
		QGraphicsScene.__init__(self, parent)
		self._calendar = GraphicsCalendarItem()
		self.addItem( self._calendar )

	def mousePressEvent( self, event ):
		for item in self.items( event.scenePos() ):
			if isinstance(item, GraphicsTaskItem ):
				self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self._calendar.model().modelFromIndex(item.index() ) )

	def mouseDoubleClickEvent( self, event ):
		for item in self.items( event.scenePos() ):
			if isinstance(item, GraphicsTaskItem ):
				self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self._calendar.model().modelFromIndex(item.index() ) )
				self.emit( SIGNAL('activated()') )

	def setSize(self, size):
		self._calendar.setSize( size )
		
	def setModel(self, model):
		self._calendar.setModel( model )

	def model(self, model):
		return self.model()

	def setModelDateColumn(self, column):
		self._calendar.setModelDateColumn( column )

	def setModelTitleColumn(self, column):
		self._calendar.setModelTitleColumn( column )

	def updateData(self):
		self._calendar.updateCalendarData()
		self._calendar.updateCalendarView()

	def setStartDate(self, date):
		self._calendar.setStartDate( date )

	def setEndDate(self, date):
		self._calendar.setEndDate( date )


class GraphicsCalendarView( QGraphicsView ):
	def __init__(self, parent=None):
		QGraphicsView.__init__(self, parent)
		self._model = None
		self.setScene( GraphicsCalendarScene(self) )
		#self._calendar = GraphicsCalendarScene(self)
		#self._calendar = GraphicsCalendarItem()
		#self._calendar.setSize( self.size() )
		#self.scene().addItem( self._calendar )
		#self.scend().setSize( self.size() )

	def resizeEvent(self, event):
		self.scene().setSize( QSize( self.size().width()-20, self.size().height()-20 ) )

	def setModel(self, model):
		self.scene().setModel( model )

	def model(self, model):
		return self.scene().model()

	def setModelDateColumn(self, column):
		self.scene().setModelDateColumn( column )

	def setModelTitleColumn(self, column):
		self.scene().setModelTitleColumn( column )

	def updateData(self):
		self.scene().updateData()

	def setStartDate(self, date):
		self.scene().setStartDate( date )

	def setEndDate(self, date):
		self.scene().setEndDate( date )


(CalendarViewUi, CalendarViewBase) = loadUiType( Common.uiPath('calendarview.ui') )

class CalendarView( AbstractView, CalendarViewUi ):
	def __init__(self, parent):
		AbstractView.__init__(self, parent)
		CalendarViewUi.__init__(self)
		self.setupUi( self )
		self.connect( self.calendarWidget, SIGNAL('selectionChanged()'), self.updateCalendarView )
		self.connect( self.pushMonthlyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.connect( self.pushWeeklyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.connect( self.pushDailyView, SIGNAL('clicked()'), self.updateCalendarView )
		self.setReadOnly( True )
		self.title = ""
		self.view_type = 'calendar'
		self.updateCalendarView()
		self.connect( self.calendarView.scene(), SIGNAL('currentChanged(PyQt_PyObject)'), self.currentChanged )
		self.connect( self.calendarView.scene(), SIGNAL('activated()'), self.activated )

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
		self.calendarView.setStartDate( start )
		self.calendarView.setEndDate( end )

	def display(self, currentModel, models):
		self.calendarView.updateData()

	def currentChanged(self, obj):
		self.emit( SIGNAL('currentChanged(PyQt_PyObject)'), obj )

	def activated( self ):
		self.emit( SIGNAL('activated()') )

