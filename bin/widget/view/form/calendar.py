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

from common import common

from abstractformwidget import *
from common.calendar import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

class DateFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		loadUi( common.uiPath('calendar.ui'), self)
		self.connect( self.pushCalendar, SIGNAL( "clicked()" ),self.showCalendar )
		self.dateTime = False
		self.connect( self.uiDate, SIGNAL('editingFinished()'), self.modified )
		self.installPopupMenu( self.uiDate )

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
		return  str(dateToStorage(date))

	def store(self):
		self.model.setValue(self.name, self.value())

	def clear(self):
		self.uiDate.setText('')
	
	def showValue(self):
		value = self.model.value(self.name)
		if value:
			self.uiDate.setText( dateToText( storageToDate( value ) ) )
		else:
			self.clear()

	def showCalendar(self):
		PopupCalendar( self.uiDate, self.dateTime )

class DateTimeFormWidget( DateFormWidget ):
	def __init__(self, parent, model, attrs={}):
		DateFormWidget.__init__( self, parent, model, attrs=attrs)
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
 		value = self.model.value(self.name)
		if value:
			self.uiDate.setText( dateTimeToText( storageToDateTime(value) ) )
		else:
			self.clear()


# There are currently no server modules using the time datatype.
class TimeFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		self.uiTime = QLineEdit( self )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiTime )
		self.installPopupMenu( self.uiTime )
		self.connect( self.uiTime, SIGNAL('editingFinished()'), self.modified )

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
		self.model.setValue(self.name, self.value())

	def clear(self):
		self.uiTime.clear()

	def showValue(self):
		value = self.model.value(self.name)
		if value:
			self.uiTime.setText( timeToText( storageToTime( value ) ) )
		else:
			self.clear()


class FloatTimeFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		self.uiTime = QLineEdit( self )
		self.uiTime.setMaxLength( 11 )
		self.uiTime.setVisible(not attrs.get('invisible', False))
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.uiTime )
		self.installPopupMenu( self.uiTime )
		self.connect( self.uiTime, SIGNAL('editingFinished()'), self.modified )

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
		self.model.setValue(self.name, textToFloatTime(unicode(self.uiTime.text())) )

	def clear(self):
		self.uiTime.setText('00:00')

	def showValue(self):
		value = self.model.value(self.name)
		if value:
			self.uiTime.setText( floatTimeToText( value ) )
		else:
			self.uiTime.setText( '00:00' )
