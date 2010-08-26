##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L. 
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

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *

from Koo import Rpc
from Koo.Common import Api

class HelpWidget( QWebView ):

	FieldType = 1
	ViewType = 2
	MenuType = 3

	def __init__(self, parent=None):
		QWebView.__init__(self, parent)
		self.setWindowFlags( Qt.Popup )
		self.setFixedSize( 600, 400 )
		self.manager = Rpc.RpcNetworkAccessManager( self.page().networkAccessManager() )
		self.page().setNetworkAccessManager( self.manager )
		self.page().setLinkDelegationPolicy( QWebPage.DelegateExternalLinks )
		self.connect( self, SIGNAL( 'linkClicked(QUrl)' ), self.openLink )

		# Determine appropiate position for the popup
		screenHeight = QApplication.desktop().screenGeometry().height()
		screenWidth = QApplication.desktop().screenGeometry().width()
		pos = parent.parent().mapToGlobal( parent.pos() )

		# Fix y coordinate
		y = pos.y() + parent.height()
		if y + self.height() > screenHeight:
			y = pos.y() - self.height()
			if y < 0:
				y = screenHeight - self.height()
		# Fix x coordinate
		x = pos.x()
		if x < 0:
			x = 0
		elif x + self.width() > screenWidth:
			x = screenWidth - self.width()

		self.move( x, y )

		self._label = ''
		self._help = ''
		self._filter = ()
		self._type = None

	def setLabel(self, text):
		self._label = text
		self.updateText()

	def setHelp(self, text):
		self._help = text
		self.updateText()
	
	def setFilter(self, filter):
		self._filter = filter
		self.updateText()

	def setType(self, type):
		self._type = type
		self.updateText()

	def openLink(self, url):
		Api.instance.createWebWindow( unicode( url.toString() ), _('Documentation') )
		self.hide()

	def updateText(self):
		if not self._type:
			return
		if self._filter:
			if self._type == self.FieldType:
				function = 'get_field_headings'
			elif self._type == self.ViewType:
				function = 'get_view_headings'
			else:
				function = 'get_menu_headings'
			headings = Rpc.session.execute('/object','execute','ir.documentation.paragraph', function, self._filter, Rpc.session.context)
		else:
			headings = []

		print "HEADINGS: ", [x[:10] for x in headings]
		htmlHeadings = []
		for heading in headings:
			html = '<div style="spacing: 20px; padding: 2px; background-color: Lavender;"><p><small><a style="text-decoration:none;" href="openerp://ir.documentation.file/get/index.html#%s">%s</a></small></p></div>' % (heading[0], heading[1])
			html = html.replace('\\n','')
			htmlHeadings.append( html )

		


		if htmlHeadings:
			foundMessages = {
				self.FieldType : _('<p><i>The following sections in the documentation refer to this field:</i></p>'),
				self.ViewType : _('<p><i>The following sections in the documentation refer to this view:</i></p>'),
				self.MenuType : _('<p><i>The following sections in the documentation refer to this menu entry:</i></p>'),
			}
			references = foundMessages[self._type]
			references += '\n'.join( htmlHeadings )
		else:
			notFoundMessages = {
				self.FieldType : _('<p><i>No sections in the documentation refer to this field.</i></p>'),
				self.ViewType : _('<p><i>No sections in the documentation refer to this view.</i></p>'),
				self.MenuType : _('<p><i>No sections in the documentation refer to this menu entry.</i></p>'),
			}
			references = notFoundMessages[self._type]
			
		html = '<html><body style="background-color: #FFFFF0"><p><b>%s</b></p><p>%s</p><p>%s</p></body></html>' % (self._label, self._help, references)
		self.setHtml( html )

