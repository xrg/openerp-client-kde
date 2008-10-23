##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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

import gettext

import Rpc
import os
import sys
import logging
from options import options

from PyQt4.QtCore  import  *
from PyQt4.QtGui import *
from PyQt4.uic import *

from paths import *



# Load Resource
QResource.registerResource( uiPath( "common.rcc" ) )

## Returns a dictionary with all the attributes found in a XML with their 
# name as key and the corresponding value.
def node_attributes(node):
   result = {}
   attrs = node.attributes
   if attrs is None:
	return {}
   for i in range(attrs.length):
	result[attrs.item(i).localName] = attrs.item(i).nodeValue
   return result

## @brief The SelectionDialog class shows a dialog prompting the user to choose
# among a list of items.
#
# The selected value is stored in the 'result' property.
# @see selection()
class SelectionDialog(QDialog):	
	def __init__(self, title, values, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath( 'win_selection.ui' ), self )
		if title:
			self.uiTitle.setText( title )
		for x in values.keys():
			item = QListWidgetItem()
			item.setText(x)
			item.setData(Qt.UserRole, QVariant(values[x]))
			self.uiList.addItem( item )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.selected )

	def selected(self):
		self.result = ""
		item = self.uiList.currentItem()
		self.result = ( unicode(item.text()), unicode(item.data(Qt.UserRole).toString()) )
		self.accept()

## @brief Shows the SelectionDialog
#
# It returns the selected item or False if none was selected.
#
# No dialog will be shown if the dictionary of values is empty. If alwaysask 
# is False (the default) no dialog is shown and the only element is returned
# as selected.
def selection(title, values, alwaysask=False):
	if len(values) == 0:
		return None
	elif len(values)==1 and (not alwaysask):
		key = values.keys()[0]
		return (key, values[key])
	s = SelectionDialog(title, values)
	if s.exec_() == QDialog.Accepted:
		return s.result
	else:
		return False
	

## @brief The TipOfTheDayDialog class shows a dialog with a Tip of the day
# TODO: Use KTipDialog when we start using KDE libs
class TipOfTheDayDialog( QDialog ):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		try:
			self.number = int(options.options['tip.position'])
		except:
			self.number = 0
			log = logging.getLogger('common.message')
			log.error('Invalid value for option tip.position ! See ~/.terprc !')
	
		loadUi( uiPath('tip.ui'), self )	
		self.connect( self.pushNext, SIGNAL('clicked()'), self.nextTip )
		self.connect( self.pushPrevious, SIGNAL('clicked()'), self.previousTip )
		self.connect( self.pushClose, SIGNAL('clicked()'), self.closeTip )
		self.uiShowNextTime.setChecked( options.options['tip.autostart'] )
		self.showTip()
	
	def showTip(self):
		tips = file(kPath('ktinytips.txt')).read().split('---')
		tip = tips[self.number % len(tips)]
		del tips
		self.uiTip.setText(tip)

	def nextTip(self):
		self.number+=1
		self.showTip()

	def previousTip(self):
		if self.number>0:
			self.number -= 1
		self.showTip()

	def closeTip(self):
		options.options['tip.autostart'] = self.uiShowNextTime.isChecked()
		options.options['tip.position'] = self.number+1
		options.save()
		self.close()


## @brief The SupportDialog class shows the support dialog.
#
# Currently, doesn't allow to send support requests, so we should consider
# implmenting this or simply removing it.
# @see support()
# TODO: Decide about the future of this class.
class SupportDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('support.ui'), self )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.send )

	def send(self):
		QMessageBox.information(self, '', _('Sending support requests is not available with the TinyERP KDE client'))

## @brief Shows the SupportDialog
def support():
	dialog = SupportDialog()
	dialog.exec_()

# Function used by the notifier in the KTiny application
def warning(title, message):
	QApplication.setOverrideCursor( Qt.ArrowCursor )
	QMessageBox.warning(None, title, message)
	QApplication.restoreOverrideCursor()

## @brief The ErrorDialog class shows the error dialog used everywhere in KTiny.
#
# The dialog shows two tabs. One with a short description of the problem and the
# second one with the details, usually a backtrace.
#
# @see error()
class ErrorDialog( QDialog ):
	def __init__(self, title, message, details='', parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('error.ui'), self )
		self.uiDetails.setText( details )
		self.uiErrorInfo.setText( message )
		self.uiErrorTitle.setText( title )
		QApplication.changeOverrideCursor( Qt.ArrowCursor )
	
	def done(self, r):
		QApplication.restoreOverrideCursor()
		QDialog.done(self, r)


## @brief Shows the ErrorDialog 
def error(title, message, details=''):
	log = logging.getLogger('common.message')
	log.error('MSG %s: %s' % (unicode(message),details))
	dialog = ErrorDialog( unicode(title), unicode(message), unicode(details) )
	dialog.exec_()
		
## @brief The ProgressDialog class shows a progress bar moving left and right until you stop it.
#
# To use it:
# 1) Create a dialog (eg. dlg = ProgressDialog(self))
# 2) Call the start function (eg. dlg.start() )
# 3) Call the stop function when the operation has finished (eg. dlg.stop() )
# Take into account that the dialog will only show after a couple of seconds. This way, it
# only appears on long running tasks.
class ProgressDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('progress.ui'), self )
		self.progressBar.setMinimum( 0 )
		self.progressBar.setMaximum( 0 )
		
	def start(self):
		self.timer = QTimer()
		self.connect( self.timer, SIGNAL('timeout()'), self.timeout )
		self.timer.start( 2000 )

	def timeout(self):
		self.timer.stop()
		self.show()
		
	def stop(self):
		self.timer.stop()
		self.accept()

