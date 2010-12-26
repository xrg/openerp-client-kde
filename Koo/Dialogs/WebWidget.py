##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. All rights reserved
#                    http://www.NaN-tic.com
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

from Koo import Rpc

from Koo.Common import Common
from Koo.Common.Settings import *
from Koo.Common import Help

from PyQt4.QtWebKit import * 
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

(WebWidgetUi, WebWidgetBase) = loadUiType( Common.uiPath('webcontainer.ui') )

class WebWidget( QWidget, WebWidgetUi ):
	# form constructor:
	# model -> Name of the model the form should handle
	# res_id -> List of ids of type 'model' to load
	# domain -> Domain the models should be in
	# view_type -> type of view: form, tree, graph, calendar, ...
	# view_ids -> Id's of the views 'ir.ui.view' to show
	# context -> Context for the current data set
	# parent -> Parent widget of the form
	# name -> User visible title of the form
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		WebWidgetUi.__init__(self)
		self.setupUi( self )

		self.manager = Rpc.RpcNetworkAccessManager( self.uiWeb.page().networkAccessManager() )
		self.uiWeb.page().setNetworkAccessManager( self.manager )

		self.name = ''
		self.handlers = {
			'Previous': self.previous,
			'Next': self.next,
			'Reload': self.reload,
			'Find': self.find,
		}

	def switchViewMenu(self):
		return None

	def setUrl(self, url):
		self.uiWeb.load( url )

	def setTitle(self, title):
		if len(title) > 20:
			self.name = '%s...' % title[:20]
		else:
			self.name = title

	def find(self):
		text, ok = QInputDialog.getText( self, _('Find'), _('Find:') )
		if not ok:
			return
		self.uiWeb.findText( text, QWebPage.HighlightAllOccurrences )

	def previous(self):
		self.uiWeb.back()

	def next(self):
		self.uiWeb.forward()

	def reload(self):
		self.uiWeb.reload()

	def storeViewSettings(self):
		pass

	def closeWidget(self):
		self.screen.storeViewSettings()
		self.emit( SIGNAL('closed()') )

	def canClose(self, urgent=False):
		# Store settings of all opened views before closing the tab.
		#self.screen.storeViewSettings()
		return True

	def actions(self):
		return []

	def help(self, button):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		helpWidget = Help.HelpWidget( button )
		helpWidget.setLabel( _('No help available for web views') )
		helpWidget.setType( helpWidget.ViewType )
		helpWidget.show()
		QApplication.restoreOverrideCursor()
		return

	def __del__(self):
		pass

