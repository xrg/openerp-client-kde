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
from PyQt4.QtGui import *

## @brief The AbstractView class describes the interface Views must implement
class AbstractView(QWidget):
	def __init__(self, parent):
		QWidget.__init__( self, parent )
		# TODO: By now, needs the self.widget
		self.widget = None
		# The 'id' corresponds to the view id in the database. Not directly
		# used by the view itself might be filled and used by other classes 
		# such as Screen, which will use this id for storing/loading settings
		self.id = False
		self._onWrite = ''

	## @brief This function should return the type of view the class handles. Such as 'tree' or 'from'.
	def viewType(self):
		return None
		
	def __del__(self):
		import logging
		logging.getLogger('koo.view').debug("View being deleted %s, %s", self.id, str(self))

	## @brief This function should store the information in the model
	# The model used should be the one given by display()
	# which will always have been called before store().
	def store(self):
		pass
	
	## @brief This function should display the information of the model or models
	# currentRecord points to the record (object Record) that is currently selected
	# models points to the model list (object RecordGroup) 
	# Example: forms only use the currentModel, while tree & charts use models
	def display(self, currentRecord, models):
		pass
	
	## @brief Not used in the TreeView, used in the FormView to
	# set all widgets to the state of 'valid'
	def reset(self):
		pass

	## @brief Should return a list with the currently selected 
	# records in the view. If the view is a form, for example,
	# the current id is returned. If it's a tree with
	# several items selected, returns all of them.
	def selectedRecords(self):
		return []

	## @brief Selects the current record
	def setSelected(self, record):
		pass

	## @brief This function should return False if the view modifies data
	# or True if it doesn't
	def isReadOnly(self):
		return True

	## @brief This function should be implemented if the view can be
	# configured to be read-only or read-write.
	def setReadOnly(self, value):
		return 

	## @brief Override this function in your view if you wish to store
	# some settings per user and view. The function should return
	# a python string with all the information which should be
	# parseable afterwords by setViewSettings().
	def viewSettings(self):
		return ''

	## @brief Override this function in your view if you wish to restore
	# a previous configuration. The function will be called when
	# necessary. The string given in 'settings' will be one 
	# previously returned by viewSettings().
	def setViewSettings(self, settings):
		pass

	## @brief Should return True if the view is capable of showing multiple records
	# or False if it can only show one.
	#
	# For example, tree will return True whereas 'form' will return False.
	# The default implementation returns True.
	def showsMultipleRecords(self):
		return True

	## @brief Start editing current record.
	#
	# Some views (such as TreeView) need a way of being told to start edit mode.
	# Such is the case when a new record is created as we want TreeView to start
	# editing the newly created record. Other views such as form can simply ignore
	# this call.
	def startEditing(self):
		return 

	## @brief Returns True if new records should be added at the top of the list
	# or False if they should be added at the bottom (the default).
	def addOnTop(self):
		return False

	## @brief Returns the on_write function.
	#
	# This server side function can be configured in the view so it's called each 
	# time a record is created or written.
	def onWriteFunction(self):
		return self._onWrite

	## @brief Establishes the name of the on_write function.
	#
	# By default it's the empty string, so no function will be called on the server.
	def setOnWriteFunction(self, value):
		self._onWrite = value

