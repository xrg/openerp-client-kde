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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

def flatten(x):
	"""flatten(sequence) -> list

	Returns a single, flat list which contains all elements retrieved
	from the sequence and all recursively contained sub-sequences
	(iterables).

	Examples:
	>>> [1, 2, [3,4], (5,6)]
	[1, 2, [3, 4], (5, 6)]
	>>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
	[1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""
	result = []
	for el in x:
		#if isinstance(el, (list, tuple)):
		if hasattr(el, "__iter__") and not isinstance(el, basestring):
			result.extend(flatten(el))
		else:
			result.append(el)
	return result

class ColorManager:
	colorList = [ QColor('#%02x%02x%02x' % (25+((r+10)%11)*23,5+((g+1)%11)*20,25+((b+4)%11)*23) ) for r in range(11) for g in range(11) for b in range(11) ]

	def __init__(self, count):
		self.list = ColorManager.pickColors(count)

	def pen(self, i):
		return QPen( self.edgeColor(i) )

	def brush(self, i):
		g = QLinearGradient(0, 0, 200, 200)
		g.setColorAt( 0.0, self.color(i) )
		color = self.color(i)
		edge = QColor()
		edge.setRed( min( color.red()+45, 255 ) )
		edge.setGreen( min( color.green()+45, 255 ) )
		edge.setBlue( min( color.blue()+45, 255 ) )
		g.setColorAt( 1.0, edge )
		return QBrush( g )

	def color(self, i):
		return QColor( self.list[i] )

	# Returns the appropiate edge color for the given color
	def edgeColor( self, i ):
		color = self.color(i)
		edge = QColor()
		edge.setRed( max( color.red()-45, 0 ) )
		edge.setGreen( max( color.green()-45, 0 ) )
		edge.setBlue( max( color.blue()-45, 0 ) )
		return edge

		
	# Creates a list of colors of size n.
	# This way, colors can be as far from each other as possible
	@staticmethod
	def pickColors(n):
		if n:
			return ColorManager.colorList[0:-1:len(ColorManager.colorList)/(n+1)]
		else:
			return []

	
class LegendItem(QGraphicsItemGroup):
	# Parent must be a Chart
	def __init__(self, parent):
		QGraphicsPathItem.__init__(self, parent)
		self._labels = []
		self._rects = []
		self._texts = []
		self._background = QGraphicsPathItem(self)
		self._background.setBrush( QBrush( QColor( 230, 230, 230, 200 ) ) )
		self._background.setPen( QPen( QColor( 64, 64, 64, 200 ) ) )
		self.setZValue( 2 )
		self._chartWidth = 0

	def setChartWidth(self, width):
		self._width = width

	def chartWidth(self):
		if self._width:
			return self._width
		else:
			return self.scene().width()

	def setLabels(self, labels):
		self._labels = labels
		self.updateLabels()

	def updateLabels(self):
		self.clear()
		font = QFont()
		metrics = QFontMetrics( font )
		y = 0
		manager = ColorManager( len(self._labels) )
		maxWidth = 0
		maxHeight = 0
		for i in range(len(self._labels)):
			label = self._labels[i]

			text = QGraphicsSimpleTextItem( self )
			text.setPos( 35, y )
			text.setText( label )
			text.setZValue( 2 )
			self._texts.append( text )
			maxWidth = max( maxWidth, 35 + text.boundingRect().right() )

			rect = QGraphicsRectItem(self)
			# We use the boundingRect of letter 'N' instead of the label
			# in case there's no text available
			rect.setRect( 0, y + 2, 30, metrics.boundingRect('N').height() - 4 )
			rect.setBrush( manager.brush(i) )
			rect.setPen( manager.pen(i) )
			rect.setZValue( 2 )
			self._rects.append( rect )

			self.addToGroup( text )
			self.addToGroup( rect )

			y += metrics.lineSpacing()

		# Pick last text and rect and calculate the total hight of the legend
		maxHeight = max( text.boundingRect().bottom(), rect.boundingRect().bottom() )

		# Legend background
		path = QPainterPath()
		rect = QRectF( -5, -5, maxWidth + 10, maxHeight + 10 )
		path.addRoundedRect( rect, 5.0, 5.0 )
		self._background.setPath( path )

	def clear(self):
		for rect in self._rects:
			self.removeFromGroup( rect )
			rect.setParentItem( None )
			del rect
		self._rects = []
		for text in self._texts:
			self.removeFromGroup( text )
			text.setParentItem( None )
			del text
		self._texts = []

	def place(self):
		if not self.scene():
			return
		rect = self.mapToScene( self.boundingRect() ).boundingRect()
		rect.setX( 0 )
		rect.setWidth( self.scene().width() )

		# As we don't want the Legend (self) to be considered
		# we make it invisible as it's more efficient than removing
		# self later because all children are hidden too.
		self.setVisible( False )
		items = self.scene().items( rect ) 
		self.setVisible( True )

		# Now remove the whole chart as it takes all the space
		# in which we want to put the Legend
		if self.parentItem() in items:
			items.remove( self.parentItem() )

		def sortByX(x, y):
			i = x.mapToScene( x.boundingRect() ).boundingRect().x()
			j = y.mapToScene( y.boundingRect() ).boundingRect().x()
			if i > j:
				return 1
			elif i < j:
				return -1
			else:
				return 0

		items.sort( sortByX )
		maxWidth = 0
		maxWidthPosition = 0
		for x in range(len(items)+1):
			if x > 0:
				i = items[x-1].mapToScene( items[x-1].boundingRect() ).boundingRect().right()
			else:
				i = 0
			if x < len(items):
				j = items[x].mapToScene( items[x].boundingRect() ).boundingRect().x()
			else:
				j = self.chartWidth()
			width = j - i
			if maxWidth < width:
				maxWidth = width
				maxWidthPosition = i
		self.setPos( maxWidthPosition + maxWidth / 2 - self.boundingRect().width() / 2, self.pos().y() )


class AbstractChart(QGraphicsItemGroup):
	colorList = [ QColor('#%02x%02x%02x' % (25+((r+10)%11)*23,5+((g+1)%11)*20,25+((b+4)%11)*23) ) for r in range(11) for g in range(11) for b in range(11) ]

	def __init__(self, parent=None):
		QGraphicsItemGroup.__init__(self, parent)
		self._values = []
		self._labels = []
		self._categories = []
		self._items = []
		self._showLegend = True
		self._legend = LegendItem( self )
		self._legend.setPos( 300, 5 )
		self._size = QSize( 200, 200 )

	def setSize( self, size ):
		self._size = size
		self._legend.setChartWidth( self._size.width() )
		self.updateChart()

	def height(self):
		return self._size.height() 

	def width(self):
		return self._size.width()

	def setValues( self, values ):
		self.clear()
		self._values = values
		self.updateChart()

	def setLabels( self, labels ):
		self._labels = labels
		self._legend.setLabels( labels )
		self.updateToolTips()
		self.updateChart()

	# To be implemented by subclasses
	def updateChart(self):
		pass

	def setShowLegend( self, show ):
		self._showLegend = show

	def updateToolTips(self):
		if len(self._items) != len(self._labels):
			return
		for x in range(len(self._items)):
			self._items[x].setToolTip( self._labels[x] )

	def clear(self):
		for item in self._items:
			self.removeFromGroup( item )
			del item
		self._items = []

