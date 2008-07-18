#   Copyright (C) 2008 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or 
#   (at your option) any later version. 
#
#   This program is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License 
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 

from PyQt4.QtGui import *
from abstractchart import *


class PieChartSector(QGraphicsEllipseItem):
	def __init__(self, parent):
		QGraphicsEllipseItem.__init__(self, parent)
		self.label = None

class PieChart(AbstractChart):
	def __init__(self, parent=None):
		AbstractChart.__init__(self, parent)

	def setValues( self, values ):
		self.clear()
		values = flatten(values)
		self._values = values
		self.updateChart()

	def updateChart(self):
		self.clear()
		total = sum(self._values)

		lastAngle = 0
		manager = ColorManager( len(self._values) )
		for i in range(len(self._values)):
			value = self._values[i]
			angle = ( value / total ) * ( 360 * 16 )

			item = PieChartSector( self )
			item.labelId = i
			item.setBrush( manager.brush(i) )
			item.setPen( manager.pen(i) )
			size = min( self._size.width(), self._size.height() )
			item.setRect( 0, 0, size, size )
			item.setStartAngle( lastAngle )
			item.setSpanAngle( angle )
			self.addToGroup( item )
			self._items.append( item )

			lastAngle += angle
		self.updateToolTips()

	def setData(self, data):
		# Admited data structure:
		#[ { 'name': 'A', 'value': 2 }, { 'name': 'B', 'value': 8 } ]
		labels = []
		values = []
		for x in data:
			labels.append( x['name'] )
			values.append( x['value'] )
		self.setValues( values )
		self.setLabels( labels )

