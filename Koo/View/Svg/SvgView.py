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

from Koo.View.AbstractView import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *

class SvgView( AbstractView ):
	def __init__(self, parent=None):
		AbstractView.__init__( self, parent )
		self.scene = QGraphicsScene( self )
		self.view = QGraphicsView( self )
		self.view.setScene( self.scene )
		self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform);
		self.view.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.view.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.svg = None
		self.widgets = {}
		self.fields = {}
		self.record = None

		layout = QVBoxLayout(self)
		layout.addWidget( self.view )

	def viewType(self):
		return 'gantt'

	def showsMultipleRecords(self):
		return False

	def setSvg( self, file ):
		#t = self.view.transform()
		#t.scale( 2, 2 )
		#self.view.setTransform( t )

		self.svg = QGraphicsSvgItem( file )
		self.scene.addItem( self.svg )

		for name in self.widgets.keys():
			if not self.svg.renderer().elementExists( name ):
				continue
			r = self.svg.renderer().boundsOnElement( name )
			#matrix = self.svg.renderer().matrixForElement( name )
			widget = self.widgets[name]
			widget.resize( r.size().width(), r.size().height() )
			proxy = self.scene.addWidget( widget )
			proxy.resize( r.size() )
			#proxy.setTransform( QTransform( matrix ) )
			proxy.moveBy( r.x(), r.y() )
			proxy.setZValue( 1 )

		#self.view.fitInView( self.svg, Qt.KeepAspectRatio )

	def display(self, currentRecord, records):
		# Though it might seem it's not necessary to connect FormView to recordChanged signal it
		# actually is. This is due to possible 'on_change' events triggered by the modification of
		# a field. This forces those widgets that might change the record before a 'lostfocus' has been
		# triggered to ensure the view has saved all its fields. As an example, modifying a char field
		# and pressing the new button of a OneToMany widget might trigger a recordChanged before 
		# char field has actually changed the value in the record. After updateDisplay, char field will
		# be reset to its previous state. Take a look at OneToMany implementation to see what's needed
		# in such buttons.
		if self.record:
			self.disconnect(self.record,SIGNAL('recordChanged(PyQt_PyObject)'),self.updateDisplay)
		self.record = currentRecord
		if self.record:
			self.connect(self.record, SIGNAL('recordChanged(PyQt_PyObject)'),self.updateDisplay)
		self.updateDisplay(self.record)

	def updateDisplay(self, record):
		# Update data on widgets
		for name in self.widgets:
			if self.record:
				self.widgets[name].load(self.record)
			else:
				self.widgets[name].load(None)
