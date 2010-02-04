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
from Koo.KooChart import ColorManager
import math


class GraphicsTaskItem( QGraphicsRectItem ):
	# Parent should be a GraphicsDayItem
	def __init__(self, parent=None):
		QGraphicsRectItem.__init__(self, parent)
		self.setFlag( QGraphicsItem.ItemClipsChildrenToShape, True )
		self._text = QGraphicsTextItem( self )
		self._text.setZValue( 1 )
		self.setSize( QSize(100, 100) )
		self._index = None
		self._start = ''
		self._duration = ''
		self._backgroundColor = QColor( 200, 250, 200 )
		self._edgeColor = QColor( 100, 200, 100 )
		self.setActive( False )

	def setBackgroundColor(self, color):
		self._backgroundColor = color
		self.updateColors()

	def setEdgeColor(self, color):
		self._edgeColor = color
		self.updateColors()
		
	def setActive(self, active):
		self._active = active
		self.updateColors()

	def isActive(self):
		return self_active

	def setSize(self, size):
		self._size = size
		self._text.setTextWidth( self._size.width() )
		self.setRect( 0, 0, size.width(), size.height() )

	def setTitle(self, title):
		self._title = title
		self._text.setPlainText( title )
		self.updateToolTip()

	def setIndex(self, index):
		self._index = index

	def index(self):
		return self._index

	def updateColors(self):
		if self._active:
			self.setBrush( QBrush( QColor( 250, 200, 200 ) ) )
			self.setPen( QPen( QColor( 200, 100, 100 ) ) )
		else:
			self.setBrush( self._backgroundColor )
			self.setPen( self._edgeColor )
		
	def updateToolTip(self):
		text = _('<b>%(title)s</b><br/><b>Start:</b> %(start)s<br/><b>Duration:</b> %(duration)s<br/>') % { 
			'title': self._title, 
			'start': self._start, 
			'duration': self._duration 
		}
		self.setToolTip( text )

	def setStart(self, start):
		self._start = start
		self.updateToolTip()

	def setDuration(self, duration):
		self._duration = duration
		self.updateToolTip()
		

class GraphicsDayItem( QGraphicsItemGroup ):
	colorManager = ColorManager( 30 )

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
		title = '<center>%s</center>' % ( unicode(self._date.toString()) )
		self._title.setHtml( title )
		for index in self._tasks.keys():
			task = self._tasks[index] 
			model = index.model()
			titleIdx = model.index( index.row(), self.parentItem()._modelTitleColumn )
			dateIdx = model.index( index.row(), self.parentItem()._modelDateColumn )
			task.setTitle( titleIdx.data().toString() )
			task.setStart( dateIdx.data().toString() )

			if self.parentItem()._modelColorColumn >= 0:
				colorIdx = model.index( index.row(), self.parentItem()._modelColorColumn )
				task.setBackgroundColor( GraphicsDayItem.colorManager.color( colorIdx.data().toInt()[0] ) )
				task.setEdgeColor( GraphicsDayItem.colorManager.edgeColor( colorIdx.data().toInt()[0] ) )
			if self.parentItem()._hasDurationColumn:
				durationIdx = model.index( index.row(), self.parentItem()._modelDurationColumn )
				task.setDuration( durationIdx.data().toString() )
				durationTime, ok = durationIdx.data( self.parentItem().ValueRole ).toDouble()
			else:
				task.setDuration( '--' )
				durationTime = 1.0

			startTime = self.parentItem().dateTimeFromIndex( dateIdx ).time()

			height = self._size.height()

			# Position
			secs = QTime( 0, 0 ).secsTo( startTime )
			y = QTime( 0, 0 ).secsTo( startTime ) * height / 86400.0
			task.setPos( 0, y )

			# Size
			secs = durationTime * 3600.0
			y = secs * height / 86400.0
			task.setSize( QSize( self._size.width(), y ) )

			title = unicode( titleIdx.data().toString() )
	
	def taskFromIndex(self, index):
		return self._tasks.get( index, None )


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
		self._modelDurationColumn = 0
		self._modelColorColumn = -1
		self._hasDurationColumn = False

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

		#
		# Filter the records, so only those in the current* month/week/day
		#   are processed (just the ones that will be shown).
		#
		# (*) We use a hack, to get events that span from the previous
		#   month, so we really are processing one month more than the
		#   days shown :(
		#
		startField = self._model.field(self._modelDateColumn)
		durationField =  self._model.field(self._modelDurationColumn)
		if startField == durationField:
			startDate = Calendar.dateToStorage( self.startDate() )
		else:
			# TODO: Based on web client hack to get spanded events.
			#	A better solution should be used someday...
			startDate = Calendar.dateToStorage( self.startDate().addMonths(-1) )
		endDate = Calendar.dateToStorage( self.endDate() )

		oldFilter = self._model.group.filter() or []
		newFilter = []
		# Ignore any (start_field, ..., ...) item from the filter.
		for x in oldFilter:
			if x[0] != startField:
				newFilter.append(x)
		# Add the start field restrictions to the new filter
		newFilter.extend([
			(startField, '>=', startDate),
			(startField, '<=', endDate),
		])
		self._model.group.setFilter(newFilter)

		# Get the data
		for x in range(self._model.rowCount()):
			idx = self._model.index( x, self._modelDateColumn )
			date = Calendar.dateToText( self.dateTimeFromIndex( idx ).date() )
			if date in self._days:
				idx = self._model.index( x, self._modelTitleColumn )
				self._days[date].addModelIndex( idx )

		# Restore the old filter
		self._model.group.setFilter(oldFilter)

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

	def setModelDurationColumn(self, column):
		self._modelDurationColumn = column
		self._hasDurationColumn = True
		self.updateCalendarData()

	def modelDurationColumn(self):
		return self._modelDurationColumn

	def setModelColorColumn(self, column):
		self._modelColorColumn = column
		self.updateCalendarData()

	def tasksFromIndex(self, index):
		tasks = []
		for item in self._days.values():
			task = item.taskFromIndex( index )
			if task:
				tasks.append( task )
		return tasks

class GraphicsCalendarScene( QGraphicsScene ):
	def __init__(self, parent=None):
		QGraphicsScene.__init__(self, parent)
		self._calendar = GraphicsCalendarItem()
		self.addItem( self._calendar )
		self._activeIndex = QModelIndex()

	def mousePressEvent( self, event ):
		self.setActiveIndex( False )
		self._activeIndex = QModelIndex()
		for item in self.items( event.scenePos() ):
			if isinstance(item, GraphicsTaskItem ):
				self._activeIndex = item.index()
				break
		self.setActiveIndex( True )
		self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self._calendar.model().recordFromIndex(self._activeIndex) )

	def setActiveIndex( self, active ):
		if not self._activeIndex.isValid():
			return
		for x in self._calendar.tasksFromIndex( self._activeIndex ):
			x.setActive( active )

	def mouseDoubleClickEvent( self, event ):
		self.setActiveIndex( False )
		self._activeIndex = QModelIndex()
		for item in self.items( event.scenePos() ):
			if isinstance(item, GraphicsTaskItem ):
				self._activeIndex = item.index()
				break
		self.setActiveIndex( True )
		self.emit( SIGNAL("currentChanged(PyQt_PyObject)"), self._calendar.model().recordFromIndex(self._activeIndex) )
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

	def setModelDurationColumn(self, column):
		self._calendar.setModelDurationColumn( column )

	def setModelColorColumn(self, column):
		self._calendar.setModelColorColumn( column )

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

	def setModelDurationColumn(self, column):
		self.scene().setModelDurationColumn( column )

	def setModelColorColumn(self, column):
		self.scene().setModelColorColumn( column )

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
		self.updateCalendarView()
		self.connect( self.calendarView.scene(), SIGNAL('currentChanged(PyQt_PyObject)'), self.currentChanged )
		self.connect( self.calendarView.scene(), SIGNAL('activated()'), self.activated )

	def viewType(self):
		return 'calendar'

	def setModel(self, model):
		self.calendarView.setModel( model )

	def setModelDateColumn(self, column):
		self.calendarView.setModelDateColumn( column )

	def setModelTitleColumn(self, column):
		self.calendarView.setModelTitleColumn( column )

	def setModelDurationColumn(self, column):
		self.calendarView.setModelDurationColumn( column )

	def setModelColorColumn(self, column):
		self.calendarView.setModelColorColumn( column )

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

