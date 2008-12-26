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
		# Needs to set self.view_type (example: 'tree' or 'form')
		self.view_type = 'none'
		# The 'id' corresponds to the view id in the database. Not directly
		# used by the view itself might be used by filled and used by 
		# other classes such as Screen, which will use this id for storing/loading settings
		self.id = False

	## @brief This function should store the information in the model
	# The model used should be the one given by display()
	# which will always have been called before store().
	def store(self):
		pass
	
	## @brief This function should display the information of the model or models
	# currentModel points to the model (object ModelRecord) that is currently selected
	# models points to the model list (object ModelGroup) 
	# Example: forms only use the currentModel, while tree & charts use models
	def display(self, currentModel, models):
		pass
	
	## @brief Not used in the TreeView, used in the FormView to
	# set all widgets to the state of 'valid'
	def reset(self):
		pass

	## @brief Should return a list with the currently selected 
	# items in the view. If the view is a form, for example,
	# the current id is returned. If it's a tree with
	# several items selected, returns them all.
	def selectedIds(self):
		return []

	## @brief Selects the current modelId
	def setSelected(self, modelId):
		pass

	## @brief This function should return False if the view modifies data
	# or True if it doesn't
	def isReadOnly(self):
		return True

	## @brief This function should be implemented if the function can be
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

