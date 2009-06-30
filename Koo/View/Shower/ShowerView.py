##############################################################################
#
# Copyright (c) 2009 P. Christeas <p_christ@hol.gr>
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
from kshowerview import *

class ShowerView( AbstractView ):
	def __init__(self,model, parent=None):
		AbstractView.__init__( self, parent )
		print "Model:",model
		self.scene = KShowerScene(model, self )
		self.view = kshowerView(self.scene, self )
		self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform);
		self.view.setMinimumSize(200,200)
		self.view.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
		proj1 = KsmLinear(self.scene)
		proj1.setFreeMove(True);
		item1 = QGraphicsRectItem(-100,-100,100,100)
		self.scene.addItem(item1)
		proj2 = KsmLinear(self.scene)
		proj2.setSpacing(0.0,10.0)
		proj1.setChildProj(proj2)
		
		proj3 = KsmBox(self.scene)
		proj2.setChildProj(proj3)
		self.scene.setMainProjection(proj1)
		print "set all kshview"
		self.view.updateGeometry()
		self.view.show()
		print "Rect:",self.view.frameRect()

	def viewType(self):
		return 'diagram'

	def setShower( self, file ):
		pass
		
	def redraw(self):
		pass
		#self.view.show()
