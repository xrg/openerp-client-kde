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

from ShowerView import ShowerView
from Koo.View.AbstractParser import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Model import KooModel,KooModelDbg
from Koo.Common import Common
#from Koo.Common.Numeric import *
#from Koo.Common.Calendar import *
from Koo.Common.ViewSettings import *

from kshowerview import *
import xml.dom

def _dxy2deltas(dxy):
	if dxy == 'left':
		dx, dy = -10.0, 0.0
	elif dxy == 'right':
		dx, dy = 10.0, 0.0
	elif dxy == 'up':
		dx, dy = 0.0, -10.0
	elif  dxy == 'down':
		dx, dy = 0.0, 10.0
	else:
		dx, dy = map(lambda x: float(x), dxy.split(',',1))
	return (dx, dy)

ELEMENT_NODE = xml.dom.Node.ELEMENT_NODE

class ShowerParser(AbstractParser):

	def create(self, viewId, parent, viewModel, rootNode, fields, filter=None):
		self.viewModel = viewModel
		self.filter = filter

		self.header = [ {'name': 'name'} ]
		# It's expected that parent will be a Screen
		screen = parent
		attrs = Common.nodeAttributes(rootNode)
		colors = []
		print "Model, Filter:", viewModel, ',', filter

		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )
		
		if attrs.get('debug',True):
			model = KooModelDbg.KooModelDbg( parent )
		else:
			model = KooModel.KooModel( parent )

		model.setMode( KooModel.KooModel.ListMode )
		#model.setMode( KooModel.KooModel.TreeMode )
		model.setReadOnly( not attrs.get('editable', False) )
		screen.group.setAllowRecordLoading( False )
		model.setRecordGroup( screen.group )

		view = ShowerView(model, parent )
		#if not view.title:
 		#	view.title = attrs.get('string', 'Unknown' )
		# view.setReadOnly( not attrs.get('editable', False) )

		#if attrs.get('editable', False) == 'top':
		#	view.setAddOnTop( True )

		rootProj = self._parseDiagram(model, view, rootNode)
		assert rootProj, "No main projection found in <diagram>"

		print "Diagram fields:", fields.keys()
		print "Diagram header:", self.header
		model.setFields( fields )
		try:
			pfields = []
			for n in self.header:
				if not fields.has_key(n['name']):
					pfields.append(n['name'])
			
			afields = {}
			if len(pfields):
				afields.update( Rpc.session.execute('/object', 
					'execute', self.viewModel, 'fields_get', 
					pfields, screen.group.context) )
				# print "Brought extra fields:", afields

			for h in self.header:
				for k in h.keys():
				    if k in ('type', 'string', 'width' ):
					afields[h['name']][k] = h[k]
			
			print "Fields to add:", afields
			screen.group.addFields(afields)
			del afields
		except Exception, e:
			print "Sth went wrong", e
			pass

		model.setFieldsOrder( [x['name'] for x in self.header] )
		model.setColors( colors )


		#proj2 = KsmLinear(self.scene)
		#proj2.setSpacing(0.0,10.0)
		#proj1.setChildProj(proj2)
		
		#proj3 = KsmBox(self.scene)
		#proj2.setChildProj(proj3)
	

		# Create the view
		self.view = view
		self.view.id = viewId
		screen.group.setAllowRecordLoading( True )
		print "Allow record loading = true"
		view.setMainProjection(rootProj)
		#self.view.setSvg( 'restaurant.svg' )
		self.view.redraw()
		return self.view

	def _parseDiagram(self, model, view, rootNode):
		# The parsing part:
		mainNod = None
		for node in rootNode.childNodes:
			if node.nodeType != xml.dom.Node.ELEMENT_NODE:
				print "Skipping",node.localName,node
				continue
			natrs = Common.nodeAttributes(node)
			itno = None
			if node.localName == 'linear':
				itno = KsmLinear(view.scene)
				try:
					dx,dy = _dxy2deltas(natrs.get('dxy','right'))
					itno.setSpacing(dx,dy)
				except:
					pass
				
				itno.setFreeMove(True)
				
				chnod = self._parseDiaNode(model, view, node)
				itno.setChildProj(chnod)
				
			#elif node.localName == 'main':
			
			else: print "Unknown node in diagram:", node.localName
			
			if itno:
				view.projections.append(itno)
			
			if itno and not natrs.get('name',False):
				if mainNod:
					raise Exception("Two unnamed nodes found in diagram")
				mainNod = itno
			
		print "main node is a ", mainNod
		return mainNod

	def _parseDiaNode(self, model, view, dNode):
		# The parsing part:
		for node in dNode.childNodes:
			itno = None
			if node.nodeType != ELEMENT_NODE:
				print "Skipping",node.localName,node
				continue
			
			natrs = Common.nodeAttributes(node)
			if node.localName == 'lincols':
				itno = KsmColumns(view.scene) # FIXME
				pbox = KsmBox(view.scene)
				view.projections.append(pbox)
				itno.setChildProj(pbox)
				for chn in node.childNodes:
					if chn.nodeType != ELEMENT_NODE:
						continue
					if chn.localName == 'field':
						chnat = Common.nodeAttributes(chn)
						self.header.append({ 'name': chnat['name']})
					
			elif node.localName == 'box':
				itno = KsmBox(view.scene)
			else: print "Unknown node in projection:", node.localName
			
			if itno: # TODO
				view.projections.append(itno)
				print "return dianode:",itno
				return itno
		return None


# vim:noexpandtab:
