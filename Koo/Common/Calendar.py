##############################################################################
#
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

## In this module you can find various functions that help calendar 
# widgets (date, time & datetime) in View.Form, View.Tree and 
# Search modules. Probably others will use them in the future. These 
# functions provide very simple ways of parsing user input, and here we define 
# the standard output format too. Also from and to Storage functions are 
# provided that ensure date and time are formated the way the storage system 
# expects.
#
# Also a calendar popup is provided for use in widgets.
#
from PyQt4.QtCore import *
from PyQt4.QtGui import * 
from PyQt4.uic import *
import math
import locale
import Common

## @brief Converts a QDate object into a Python string
def dateToText( date ):
	return str( date.toString( 'dd/MM/yyyy' ) )

## @brief Converts a QTime object into a Python string
def timeToText( time ):
	return str( time.toString( 'hh:mm:ss' ) )

## @brief Converts a QDateTime object into a Python string
def dateTimeToText( dateTime ):
	return str( dateTime.toString( 'dd/MM/yyyy hh:mm:ss' ) )

## @brief Converts a float (type floatTime) into a Python string
def floatTimeToText( value ):
	# Ensure the value is a float. This way we also accept strings here.
	value = float( value )
	t = '%02d:%02d' % (math.floor(abs(value)),round(abs(value)%1+0.01,2) * 60)
	if value<0:
		t = '-'+t
	return t

## @brief Converts a QDate object into a Python string ready to be sent to the 
# server.
def dateToStorage( date ):
	if date.isValid():
		return str( date.toString( 'yyyy-MM-dd' ) )
	else:
		return False

## @brief Converts a QTime object into a Python string ready to be sent to the 
# server.
def timeToStorage( time ):
	if time.isValid():
		return str( time.toString( 'hh:mm:ss' ) )
	else:
		return False
	
## @brief Converts a QDateTime object into a Python string ready to be sent to 
# the server.
def dateTimeToStorage( dateTime ):
	if dateTime.isValid():
		return str( dateTime.toString( 'yyyy-MM-dd hh:mm:ss' ) )
	else:
		return False

## @brief Converts a Python string or QString into a QDate object
def textToDate( text ):
	if unicode( QString( text ).trimmed() ) == '=':
		return QDate.currentDate()

	inputFormats = ["dd/MM/yyyy", "dd-MM-yyyy", 'dd-MM-yy', 'dd/MM/yy', 'dd-M-yy', 'd-M-yy', 'd-MM-yy', 'dd.MM.yyyy', 'dd.MM.yy', 'ddMMyyyy', 'ddMMyy']
	for x in inputFormats:
		date = QDate.fromString( text, x )
		if date.isValid():
			break
	return date

## @brief Converts a Python string or QString into a QTime object
def textToTime( text ):
	text = unicode( text ).strip()
	if text == '=':
		return QTime.currentTime()

	inputFormats = ['h:m:s', 'h:m', 'hh:mm:ss', 'h.m.s', 'h.m', 'h']
	for x in inputFormats:
		time = QTime.fromString( text, x )
		if time.isValid():
			break

	if not time.isValid():
		if len(text) == 4:
			# Try to convert '1234' to '12:34'
			time = QTime.fromString( '%s:%s' % ( text[0:2], text[2:4] ), 'h:m' )
		elif len(text) == 6:
			# Try to convert '123456' to '12:34:56'
			time = QTime.fromString( '%s:%s:%s' % ( text[0:2], text[2:4], text[4:6] ), 'h:m:s' )
	return time

## @brief Converts a Python string or QString into a QDateTime object
def textToDateTime( text ):
	if unicode( QString( text ).trimmed() ) == '=':
		return QDateTime.currentDateTime()

	inputFormats = ['dd/MM/yyyy h:m:s', "dd/MM/yyyy", "dd-MM-yyyy", 'dd-MM-yy', 'dd/MM/yy', 'dd-M-yy', 'd-M-yy', 'd-MM-yy', 'ddMMyyyy', 'ddMMyy' ]
	for x in inputFormats:
		datetime = QDateTime.fromString( text, x )
		if datetime.isValid():
			break
	return datetime

## @brief Converts a Python string into a float (floatTime) 
def textToFloatTime( text ):
	try:
		text = text.replace('.',':')
		if text and ':' in text:
			return round(int(text.split(':')[0]) + int(text.split(':')[1]) / 60.0,2)
		else:
			return locale.atof(text)
	except:
		return 0.0

## @brief Converts a Python string comming from the server into a QDate object
def storageToDate( text ):
	if text:
		date = QDate.fromString( text, 'yyyy-MM-dd' )
		if date.isValid():
			return date
		# Sometimes we want datetime fields to be shown in pure date widgets
		return QDateTime.fromString( text, 'yyyy-MM-dd hh:mm:ss' ).date()
	else:
		return QDate()

## @brief Converts a Python string comming from the server into a QTime object
def storageToTime( text ):
	if text:
		return QTime.fromString( text, 'h:m:s' )
	else:
		return QTime()

## @brief Converts a Python string comming from the server into a QDateTime object
def storageToDateTime( text ):
	if text:
		return QDateTime.fromString( text, 'yyyy-MM-dd h:m:s' )
	else:
		return QDateTime


(PopupCalendarUi, PopupCalendarBase) = loadUiType( Common.uiPath('datetime.ui') )

## @brief The PopupCalendarWidget class provides a simple way to show a calendar 
# where the user can pick up a date. 
#
# You simply need to call PopupCalendarWidget(widget) where widget
# should be a QLineEdit or similar. The Popup will fill in the date itself.
#
# If you want the user to be able to select date and time, specify showTime=True
# when constructing the object.
#
# You may force the pop-up to store and close with the storeOnParent() function.
#
# Of course, PopupCalendarWidget uses the other ToTime and ToText helper functions.
#
class PopupCalendarWidget(QWidget, PopupCalendarUi):
	## @brief Constructs a PopupCalendarWidget. 
	# If showTime is True, the user will be able to select the time too.
	def __init__(self, parent, showTime = False):
		QWidget.__init__(self, parent)
		PopupCalendarUi.__init__(self)
		self.setupUi( self )

		self.showTime = showTime
		if self.showTime:
			self.uiTime.setText( textToDateTime( unicode(parent.text()) ).time().toString() )
			self.connect( self.uiTime, SIGNAL('returnPressed()'), self.storeOnParent )
		else:
			self.uiTime.hide()
			self.labelTime.hide()

		self.setWindowFlags( Qt.Popup )
		self.setWindowModality( Qt.ApplicationModal )
		pos = parent.parent().mapToGlobal( parent.pos() )
		self.move( pos.x(), pos.y() + parent.height() )
		self.connect( self.uiCalendar, SIGNAL('activated(QDate)'), self.storeOnParent )
		if self.showTime:
			self.uiCalendar.setSelectedDate( textToDateTime( parent.text() ).date() )
		else:
			self.uiCalendar.setSelectedDate( textToDate( parent.text() ) )
		self.uiCalendar.setFirstDayOfWeek( Qt.Monday )
		self.show()
		if self.showTime:
			self.uiTime.setFocus()
		else:
			self.uiCalendar.setFocus()

	## @brief Stores the currently selected date (or date and time) in the parent widget
	# and closes the popup. It also emits a 'selected()' signal.
	def storeOnParent(self):
		date = self.uiCalendar.selectedDate()
		text = dateToText( date )
		if self.showTime: 
			time = textToTime( self.uiTime.text() )
			if time.isValid():
				text = text + ' ' + timeToText(time)
			else:
				text = text + ' ' + '00:00:00'
		self.parent().setText( text )
		self.emit(SIGNAL('selected()'))
		self.close()

