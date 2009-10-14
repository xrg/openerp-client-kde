#############################################################################
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
from PyQt4.QtCore import *
from Koo.Common import Api
from Koo.Plugins import *
from Koo import Rpc
import logging

## @brief The Action class is a QAction that can execute a model action. Such
# as relate, print or wizard (on the server) and plugins (on the client).
class Action(QAction):
	## @brief Creates a new Action instance given a parent.
	def __init__(self, parent):
		QAction.__init__(self, parent)
		self._data = None
		self._type = None 
		self._model = None

	## @brief Sets the data associated with the action.
	def setData(self, data):
		self._data = data

	## @brief Returns the data associated with the action.
	def data(self):
		return self._data

	## @brief Sets the type of action (such as 'print' or 'plugin')
	def setType(self, type):
		self._type = type

	## @brief Returns the type of action (such as 'print' or 'plugin')
	def type(self):
		return self._type

	## @brief Sets the model the action refers to
	def setModel(self, model):
		self._model = model

	## @brief Returns the model the action refers to
	def model(self):
		return self._model

	## @brief Executes the action (depending on its type), given the current id
	# and the selected ids.
	def execute(self, currentId, selectedIds, context):
		log = logging.getLogger('koo.action')
		log.debug('execute<%s>(%s,..)', self._type, str(currentId))
		if self._type == 'relate':
			self.executeRelate( currentId, context )
		elif self._type in ( 'action', 'print' ):
			self.executeAction( currentId, selectedIds, context )
		else:
			self.executePlugin( currentId, selectedIds, context )

	# Executes the action as a 'relate' type
	def executeRelate(self, currentId, context ):
		if not currentId:
			QMessageBox.information( self, _('Information'), _('You must select a record to use the relate button !'))
		Api.instance.executeAction(self._data, {
			'id': currentId
		}, context)

	# Executes the action as a 'relate' or 'action' type
	def executeAction(self, currentId, selectedIds, context):
		if not currentId and not selectedIds:
			QMessageBox.information(self, _('Information'), _('You must save this record to use the relate button !'))
			return False
			
		if not currentId:
			currentId = selectedIds[0]
		elif not selectedIds:
			selectedIds = [currentId]
		if self._type == 'print':
			QApplication.setOverrideCursor( Qt.WaitCursor )
		try:
			Api.instance.executeAction(self._data, { 
				'id': currentId, 
				'ids': selectedIds, 
				'model': self._model 
			}, context )
		except Rpc.RpcException:
		        print "RpcException at executeAction", e # FIXME
			pass
		if self._type == 'print':
			QApplication.restoreOverrideCursor()

	# Executes the action as a plugin type
	def executePlugin(self, currentId, selectedIds, context):
		Plugins.execute( self._data, self._model, currentId, selectedIds, context )

## @brief The ActionFactory class is a factory that creates Action objects to execute
# actions on the server. Typically those shown in the toolbar and menus for an specific 
# model
class ActionFactory:
	## @brief Creates a list of Action objects given a parent, model and definition.
	#
	# The 'definition' parameter is the 'toolbar' parameter returned by server function
	# fields_view_get.
	@staticmethod
	def create(parent, definition, model):
		if not definition:
			# If definition is not set we initialize it appropiately
			# to be able to add the 'Print Screen' action.
			definition = {
				'print': [],
				'action': [],
				'relate': []
			}

		# We always add the 'Print Screen' action.
		definition['print'].append({
			'name': 'Print Screen', 
			'string': _('Print Screen'), 
			'report_name': 'printscreen.list', 
			'type': 'ir.actions.report.xml' 
		})

		actions = []
		for icontype in ( 'print','action','relate' ):
			for tool in definition[icontype]:
				action = Action( parent )
				action.setIcon( QIcon( ":/images/%s.png" % icontype) )
				action.setText( tool['string'] )
				action.setType( icontype )
				action.setData( tool )
				action.setModel( model )

				number = len(actions)
				shortcut = 'Ctrl+'
				if number > 9:
					shortcut += 'Shift+'
					number -= 10
				if number < 10:
					shortcut += str(number)
					action.setShortcut( QKeySequence( shortcut ) )
					action.setToolTip( action.text() + ' (%s)' % shortcut )

				actions.append( action )

		plugs = Plugins.list(model)
		for p in sorted( plugs.keys(), key=lambda x:plugs[x].get('string','') ) :
			action = Action( parent )
			action.setIcon( QIcon( ":/images/exec.png" ) )
			action.setText( unicode( plugs[p]['string'] ) )
			action.setData( p )
			action.setType( 'plugin' )
			action.setModel( model )
			actions.append( action )
		return actions

