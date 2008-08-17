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

from widget.view.abstractview import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *

class ViewSvg( AbstractView ):
	def __init__(self, parent=None):
		AbstractView.__init__( self, parent )
		self.view_type = 'svg'
		self.model_add_new = False
		self.scene = QGraphicsScene( self )
		self.view = QGraphicsView( self )
		self.view.setScene( self.scene )
		self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform);
		self.svg = None

	def setSvg( self, file ):
		t = self.view.transform()
		t.scale( 2, 2 )
		self.view.setTransform( t )

		self.svg = QGraphicsSvgItem( file )
		self.scene.addItem( self.svg )

		#self.scene.addRect( self.svg.renderer().boundsOnElement( 'contacts' ) )

		#self.scene.addRect( self.svg.renderer().boundsOnElement( 'name' ) )

		
		r = self.svg.renderer().boundsOnElement( 'name' )
		#rect = QGraphicsRectItem( 0, 0, r.width(), r.height() )
		#rect = QGraphicsRectItem( r )
		matrix =  self.svg.renderer().matrixForElement( 'name' )
		#rect.setTransform( QTransform( matrix ) )
		#rect.moveBy( r.x(), r.y() )
		#self.scene.addItem( rect )

		# W: 91.067, H: 18.522, Rx: 0, Ry: 0.312
		widget = QLineEdit()
		proxy = self.scene.addWidget( widget )
		proxy.resize( QSizeF( 91.067024, 18.522 ) )
		proxy.setTransform( QTransform( matrix ) )
		proxy.moveBy( r.x(), r.y() )
		proxy.setZValue( 1 )

		# W: 156.92343, H: 121.93722
		r = self.svg.renderer().boundsOnElement( 'contacts' )
		matrix =  self.svg.renderer().matrixForElement( 'contacts' )
		widget = QListWidget()
		widget.addItem( 'Hamburguesa       3.20' )
		widget.addItem( 'Coca-cola         1.85' )
		proxy = self.scene.addWidget( widget )
		proxy.resize( QSizeF( 156.92343, 121.93722 ) )
		proxy.setTransform( QTransform( matrix ) )
		print "X: %s, Y: %s" % ( r.x(), r.y() )
		#proxy.moveBy( r.x(), r.y() )
		# X: 343.92468 Y: 177.09489"
		proxy.moveBy( 313.92468, r.y() )
		proxy.setZValue( 1 )

