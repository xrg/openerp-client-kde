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
import re
from Koo.Common import Common
from Koo.Common import Numeric
from Koo.Common import Api

from Koo import Rpc
from Koo.Model.Group import RecordGroup

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.uic import *
from PyQt4.QtWebKit import *


(FullTextSearchDialogUi, FullTextSearchDialogBase) = loadUiType( Common.uiPath('full_text_search.ui') )

## @brief The FullTextSearchDialog class shows a dialog for searching text at all indexed models.
#
# The dialog has a text box for the user input and a combo box to search at one specific
# model or all models that have at least one field indexed.
class FullTextSearchDialog( QDialog, FullTextSearchDialogUi ):
	def __init__(self, parent = None):
		QDialog.__init__( self, parent )
		FullTextSearchDialogUi.__init__( self )
		self.setupUi( self )
		
		self.setModal( True )

		self.result = None

		self.setQueriesEnabled( False, _('Loading...') )

		self.title = _('Full Text Search')
		self.title_results = _('Full Text Search (%%d result(s))')

		self.setWindowTitle( self.title )
		self.uiWeb.page().setLinkDelegationPolicy( QWebPage.DelegateAllLinks )
		self.connect( self.uiWeb, SIGNAL('linkClicked(QUrl)'), self.open )

		self.shortcuts = {}
		self.related = []
		self.limit = 10 
		self.offset = 0
		self.pushNext.setEnabled( False )
		self.pushPrevious.setEnabled( False )

		self.connect( self.uiHelp, SIGNAL('linkActivated(QString)'), self.showHelp )
		self.connect( self.pushAccept, SIGNAL( "clicked( )"), self.reject )
		self.connect( self.pushFind, SIGNAL( "clicked()"), self.find )
		self.connect( self.pushPrevious, SIGNAL( "clicked()" ), self.previous )
		self.connect( self.pushNext, SIGNAL( "clicked()" ), self.next )
		self.show()

		QApplication.setOverrideCursor( Qt.WaitCursor )
		QTimer.singleShot( 0, self.initGui )

	def showHelp(self, link):
		QApplication.postEvent( self.sender(), QEvent( QEvent.WhatsThis ) )

	def initGui(self):
		try:
			answer = Rpc.session.call('/fulltextsearch', 'indexedModels', Rpc.session.context )
			self.uiModel.addItem( _('(Everywhere)'), QVariant( False ) )	
			for x in answer:
				self.uiModel.addItem( x['name'], QVariant( x['id'] ) )
			if len(answer) == 0:
				self.setQueriesEnabled( False, _('<b>Full text search is not configured.</b><br/>Go to <i>Administration - Configuration - Full Text Search - Indexes</i>. Then add the fields you want to be indexed and finally use <i>Update Full Text Search</i>.') )
				QApplication.restoreOverrideCursor()
				return
		except:
			self.setQueriesEnabled( False, _('<b>Full text search module not installed.</b><br/>Go to <i>Administration - Modules administration - Uninstalled Modules</i> and add the <i>full_text_search</i> module.') )
			QApplication.restoreOverrideCursor()
			return
		self.setQueriesEnabled( True )
		self.uiText.setFocus()
		if QApplication.keyboardModifiers() & Qt.AltModifier:
			clipboard = QApplication.clipboard()
			if clipboard.supportsFindBuffer():
				text = clipboard.text( QClipboard.FindBuffer )
			elif clipboard.supportsSelection():
				text = clipboard.text( QClipboard.Selection )
			else:
				text = clipboard.text( QClipboard.Clipboard )
			self.uiText.setText( text )
			self.find()
		QApplication.restoreOverrideCursor()

	def setQueriesEnabled(self, value, text = ''): 
		self.uiModel.setEnabled( value )
		self.pushFind.setEnabled( value )
		self.pushAccept.setEnabled( value )
		self.uiText.setEnabled( value )
		self.uiErrorMessage.setText( text )
		self.uiErrorMessage.setVisible( not value )

	def textToQuery(self):
		q = unicode( self.uiText.text() ).strip()
		return re.sub(' +', '|', q)

	def query(self):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		if self.uiModel.currentIndex() == 0:
			model = False
		else:
			model = unicode( self.uiModel.itemData( self.uiModel.currentIndex() ).toString() )
		# We always query for limit+1 items so we can know if there will be more records in the next page
		answer = Rpc.session.execute('/fulltextsearch', 'search', self.textToQuery(), self.limit+1, self.offset , model, Rpc.session.context)
		if len(answer) < self.limit:
			self.pushNext.setEnabled( False )
		else:
			# If there are more pages, we just show 'limit' items.
			answer = answer[:-1]
			self.pushNext.setEnabled( True )
		if self.offset == 0:
			self.pushPrevious.setEnabled( False )
		else:
			self.pushPrevious.setEnabled( True )
		self.showResults( answer )
		QApplication.restoreOverrideCursor()

	def showResults(self, answer):
		number = 1
		page = ''
		for item in answer:
			# Prepare relations
			related = Rpc.session.execute('/object', 'execute', 'ir.values', 'get', 'action', 'client_action_relate', [(item['model_name'], False)], False, Rpc.session.context)
			actions = [x[2] for x in related]
			block = []
			related = ''
			for action in actions:
				f = lambda action: lambda: self.executeRelation(action)
				action['model_name'] = item['model_name']
				self.related.append( action )
				block.append( "<a href='relate/%d/%d'>%s</a>" % ( len(self.related)-1, item['id'], action['name'] ) )
				if len(block) == 3:
					related += '<div>%s</div>' % ' - '.join( block )
					block = []
			if block:
				related += '<div>%s</div>' % ' - '.join( block )

			# Prepare URL
			url = 'open/%s/%s' % ( item['model_name'], item['id'] )

			# Prepare Shortcut
			# TODO: Implement shortcuts
			#if number <= 10:
				#self.shortcut = QShortcut( self )
				#self.shortcut.setKey( 'Ctrl+%s' % number )
				#self.shortcut.setContext( Qt.WidgetWithChildrenShortcut )
				#self.connect( self.shortcut, SIGNAL('activated()'), self.openShortcut )
				#self.shortcuts[ self.shortcut ] = url
				#shortcut = ' - <span style="color: green; font-size: medium">[Ctrl+%d]</span>' % ( number % 10 )
			#else:
				#shortcut = ''
			shortcut = ''
			number += 1

			# Prepare Item
			page += """
				<div style="padding: 5px; font-size: large">
				<a href="%(url)s">%(model_label)s: %(name)s</a> &nbsp;%(shortcut)s - <span style="font-size: medium">[ %(ranking).2f ]</span></a>
				<div style="font-size: medium">%(headline)s</div>
				<div style="font-size: medium">%(related)s</div>
				</div>""" % {
				'url': url,
				'model_label': item['model_label'],
				'name': item['name'],
				'shortcut': shortcut,
				'ranking': item['ranking'],
				'headline': item['headline'],
				'related': related,
			}

		page = '<html>%s</html>' % page
		self.uiWeb.page().mainFrame().setHtml( page )
		#self.serverOrder = ['id', 'model_id', 'model_name', 'model_label', 'name', 'headline', 'ranking']
		
	def previous(self):
		self.offset = max(0, self.offset - self.limit )
		self.query()
		
	def next(self):
		self.offset = self.offset + self.limit
		self.query()

	def find(self):
		self.offset = 0
		self.query()

	def openShortcut( self ):
		self.open( self.shortcuts[ self.sender() ] )

	def open( self, url ):
		url = unicode( url.toString() )
		url = url.split('/')
		if url[0] == 'open':
			self.result = {
				'id': int(url[2]),
				'model': url[1],
			}
			self.accept()
		elif url[0] == 'relate':
			self.executeRelation( self.related[ int(url[1]) ], int(url[2]) )
			self.reject()
	
	def executeRelation(self, action, id):
		group = RecordGroup( action['model_name'] )
		group.load( [id] )
		record = group.modelByIndex( 0 )
		action['domain'] = record.evaluateExpression( action['domain'], checkLoad=False)
		action['context'] = str( record.evaluateExpression( action['context'], checkLoad=False) )
		Api.instance.executeAction( action )

# vim:noexpandtab:
