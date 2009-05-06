##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.Common import Common
from Koo.Common import Shortcuts

from Koo.Fields.AbstractFieldWidget import *
from Koo.Fields.AbstractFieldDelegate import *
from Koo.Common.Calendar import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(DateFieldWidgetUi, DateFieldWidgetBase ) = loadUiType( Common.uiPath('calendar.ui') ) 

class DateFieldWidget(AbstractFieldWidget, DateFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		DateFieldWidgetUi.__init__(self)
		self.setupUi(self)

		# Add shortcut
		self.scSearch = QShortcut( self.uiDate )
		self.scSearch.setKey( Shortcuts.SearchInField )
		self.scSearch.setContext( Qt.WidgetShortcut )
		self.connect( self.scSearch, SIGNAL('activated()'), self.showCalendar )

		self.connect( self.pushCalendar, SIGNAL( "clicked()" ),self.showCalendar )
		self.dateTime = False
		self.connect( self.uiDate, SIGNAL('editingFinished()'), self.updateValue )
		self.installPopupMenu( self.uiDate )

	def updateValue(self):
		self.modified()
		self.showValue()

	def menuEntries(self):
		return [ (_('Set current date'), self._setCurrentDate, True ) ]	

	def _setCurrentDate( self ):
		self.uiDate.setText( dateToText( QDate.currentDate() ) )

	def colorWidget(self):
		return self.uiDate

	def setReadOnly(self, value):
		self.uiDate.setEnabled( not value )
		self.pushCalendar.setEnabled( not value )

	def value(self):
		date = textToDate( self.uiDate.text() )
		if not date.isValid():
			return False
		return dateToStorage(date)

	def store(self):
		# We've found in account.reconcile model that the date widget
		# is used to show a datetime field. The field is read-only, but when we
		# call store() it's stored without time information and this causes the 
		# record to be marked as modified. So we ensure the field is not stored
		# if it's read-only. We do it in this field only to avoid regressions 
		# with other models of the ERP.
		if self.isReadOnly():
			return
		self.record.setValue(self.name, self.value())

	def clear(self):
		self.uiDate.setText('')
	
	def showValue(self):
		value = self.record.value(self.name)
		if value:
			self.uiDate.setText( dateToText( storageToDate( value ) ) )
		else:
			self.clear()

	def showCalendar(self):
		popup = PopupCalendarWidget( self.uiDate, self.dateTime )
		self.connect( popup, SIGNAL('selected()'), self.store )

class DateTimeFieldWidget( DateFieldWidget ):
	def __init__(self, parent, model, attrs={}):
		DateFieldWidget.__init__( self, parent, model, attrs=attrs)
	 	self.dateTime = True

	def menuEntries(self):
		return [ (_('Set current date and time'), self._setCurrentDateTime, True ) ]	

	def _setCurrentDateTime( self ):
		self.uiDate.setText( dateTimeToText( QDateTime.currentDateTime() ) )

 	def value(self):
		datetime = textToDateTime( self.uiDate.text() )
		if not datetime.isValid():
			return False
		return  str(dateTimeToStorage( datetime ))
	
	def clear(self):
		self.uiDate.setText('')

 	def showValue(self):
 		value = self.record.value(self.name)
		if value:
			self.uiDate.setText( dateTimeToText( storageToDateTime(value) ) )
		else:
			self.clear()


# There are currently no server modules using the time datatype.
class TimeFieldWidget(AbstractFieldWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		self.uiTime = QLineEdit( self )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiTime )
		self.installPopupMenu( self.uiTime )
		self.connect( self.uiTime, SIGNAL('editingFinished()'), self.updateValue )

	def updateValue(self):
		self.modified()
		self.showValue()

	def menuEntries( self ):
		return [ (_('Set current time'), self.setCurrentTime, True ) ]

	def setCurrentTime( self ):
		self.uiTime.setText( timeToText( QTime.currentTime() ) )

	def setReadOnly(self, value):
		self.uiTime.setEnabled(not value)

	def colorWidget(self):
		return self.uiTime

	def value(self):
		time = textToTime( self.uiTime.text() )
		if not time.isValid():
			return False
		return timeToStorage( time )

	def store(self):
		self.record.setValue(self.name, self.value())

	def clear(self):
		self.uiTime.clear()

	def showValue(self):
		value = self.record.value(self.name)
		if value:
			self.uiTime.setText( timeToText( storageToTime( value ) ) )
		else:
			self.clear()

class FloatTimeFieldWidget(AbstractFieldWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		self.uiTime = QLineEdit( self )
		self.uiTime.setMaxLength( 11 )
		self.uiTime.setVisible(not attrs.get('invisible', False))
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiTime )
		self.installPopupMenu( self.uiTime )
		self.connect( self.uiTime, SIGNAL('editingFinished()'), self.updateValue )

	def updateValue(self):
		self.modified()
		self.showValue()

	def menuEntries( self ):
		return [ (_('Set current time'), self.setCurrentTime, True ) ]

	def setCurrentTime( self ):
		self.uiTime.setText( timeToText( QTime.currentTime() ) )

	def setReadOnly(self, value):
		self.uiTime.setEnabled(not value)

	def colorWidget(self):
		return self.uiTime

	def value(self):
		time = textToFloatTime( self.uiTime.text() )
		if not time.isValid():
			return False
		return timeToStorage( time )

	def store(self):
		self.record.setValue(self.name, textToFloatTime(unicode(self.uiTime.text())) )

	def clear(self):
		self.uiTime.setText('00:00')

	def showValue(self):
		value = self.record.value(self.name)
		if value:
			self.uiTime.setText( floatTimeToText( value ) )
		else:
			self.uiTime.setText( '00:00' )

class DateFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToDate( editor.text() )
		model.setData( index, QVariant( value ), Qt.EditRole )

class TimeFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToTime( editor.text() )
		model.setData( index, QVariant( value ), Qt.EditRole )

class DateTimeFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToDateTime( editor.text() )
		model.setData( index, QVariant( value ), Qt.EditRole )

class FloatTimeFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToFloatTime( editor.text() )
		value = floatTimeToTime( value )
		model.setData( index, QVariant( value ), Qt.EditRole )

