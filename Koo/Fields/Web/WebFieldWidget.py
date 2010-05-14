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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import *
from Koo.Common import Common
from Koo.Fields.AbstractFieldWidget import *

(WebFieldWidgetUi, WebFieldWidgetBase) = loadUiType( Common.uiPath('web.ui') ) 

## @brief The CookieJar class inherits QNetworkCookieJar to make a couple of functions public.
class CookieJar(QNetworkCookieJar):
	def __init__(self, parent=None):
		QNetworkCookieJar.__init__(self, parent)

	def allCookies(self):
		return QNetworkCookieJar.allCookies(self)
	
	def setAllCookies(self, cookieList):
		QNetworkCookieJar.setAllCookies(self, cookieList)

class WebFieldWidget(AbstractFieldWidget, WebFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		WebFieldWidgetUi.__init__(self)
		self.setupUi( self )
		self.cookieJar = CookieJar()
		self.uiWeb.page().networkAccessManager().setCookieJar( self.cookieJar )

	def sizeHint(self):
		size = super(WebFieldWidget, self).sizeHint()
		width = self.attrs.get('width')
		height = self.attrs.get('height')
		if width:
			size.setWidth( int(width) )
		if height:
			size.setHeight( int(height) )
		return size

	def storeValue(self):
		pass

	def clear( self ):
		self.uiWeb.setUrl(QUrl(''))

	def showValue(self):
		value = self.record.value(self.name) or ''
		url = QUrl(value)
		if not value or unicode(url.scheme()):
			self.uiWeb.setUrl( url )
		else:
			self.uiWeb.setHtml( value )

	def setReadOnly(self, value):
		AbstractFieldWidget.setReadOnly(self, value)
		# We always enable the browser so the user can use links.
		self.uiWeb.setEnabled( True )

	def saveState(self):
		cookieList = self.cookieJar.allCookies()
		raw = []
		for cookie in cookieList:
			# We don't want to store session cookies
			if cookie.isSessionCookie():
				continue
			# Store cookies in a list as a dict would occupy
			# more space and we want to minimize network bandwidth
			if Common.isQtVersion45():
				isHttpOnly = str(cookie.isHttpOnly())
			else:
				isHttpOnly = True
			raw.append( [
				str(cookie.name().toBase64()), 
				str(cookie.value().toBase64()), 
				unicode(cookie.path()).encode('utf-8'),
				unicode(cookie.domain()).encode('utf-8'),
				unicode(cookie.expirationDate().toString()).encode('utf-8'),
				str(isHttpOnly),
				str(cookie.isSecure()),
			])
		return QByteArray( str( raw ) )

	def restoreState(self, value):
		if not value:
			return
		raw = eval( str( value ) )
		cookieList = []
		for cookie in raw:
			name = QByteArray.fromBase64( cookie[0] )
			value = QByteArray.fromBase64( cookie[1] )
			networkCookie = QNetworkCookie( name, value )
			networkCookie.setPath( unicode( cookie[2], 'utf-8' ) )
			networkCookie.setDomain( unicode( cookie[3], 'utf-8' ) )
			networkCookie.setExpirationDate( QDateTime.fromString( unicode( cookie[4], 'utf-8' ) ) )
			if Common.isQtVersion45():
				networkCookie.setHttpOnly( eval(cookie[5]) )
			networkCookie.setSecure( eval(cookie[6]) )
			cookieList.append( networkCookie )
		self.cookieJar.setAllCookies( cookieList )
		self.uiWeb.page().networkAccessManager().setCookieJar( self.cookieJar )

# vim:noexpandtab:

