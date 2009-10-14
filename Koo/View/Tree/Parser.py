##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.View.AbstractParser import *

import time

from Koo.Model import KooModel

from TreeView import *
from PyQt4.uic import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Koo.Fields.FieldWidgetFactory import *
from Koo.Fields.FieldDelegateFactory import *
from Koo.Common import Common
from Koo.Common.Numeric import *
from Koo.Common.Calendar import *
from Koo.Common.ViewSettings import *


class TreeParser(AbstractParser):
	def create(self, viewId, parent, model, rootNode, fields):
		# It's expected that parent will be a Screen
		screen = parent

		attrs = Common.nodeAttributes(rootNode)
		
		view = TreeView( parent, attrs.get('type','tree') )
		view.id = viewId
		if 'gridwidth' in attrs:
			view.setGridWidth( int(attrs['gridwidth']) )
		if 'gridheight' in attrs:
			view.setGridWidth( int(attrs['gridheight']) )

		view.setOnWriteFunction( attrs.get('on_write', '') )

		if not view.title:
 			view.title = attrs.get('string', 'Unknown' )

		colors = []
		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )

		header = []
		columns = []
		for node in rootNode.childNodes:
			node_attrs = Common.nodeAttributes(node)
 			if node.localName == 'field':
				fname = node_attrs['name']
				twidth = {
					'integer': 60,
					'float': 80,
					'date': 70,
					'datetime': 130,
					'selection': 130,
					'char': 140,
					'one2many': 50,
				}


				if 'readonly' in node_attrs:
					fields[fname]['readonly'] = Common.stringToBool(node_attrs['readonly'])
				if 'required' in node_attrs:
					fields[fname]['required'] = Common.stringToBool(node_attrs['required'])

				if 'sum' in node_attrs and fields[fname]['type'] in ('integer', 'float', 'float_time'):
					bold = bool(int(node_attrs.get('sum_bold', 0)))
					label = node_attrs['sum']
					digits = fields.get('digits', (16,2))
					view.addAggregate( fname, label, bold, digits ) 

				node_attrs.update(fields[fname])

				visible = not eval(fields[fname].get('invisible', 'False'), {'context': screen.context})

				if 'width' in fields[fname]:
					width = int(fields[fname]['width'])
				else:
					width = twidth.get(fields[fname]['type'], 200)
				header.append( { 'name': fname, 'type': fields[fname]['type'], 'string': fields[fname].get('string', '') })
				columns.append({ 
					'width': width , 
					'type': fields[fname]['type'], 
					'attributes':node_attrs,
					'visible': visible
				})

		view.finishAggregates()

		model = KooModel.KooModel( view )
		model.setMode( KooModel.KooModel.ListMode )
		model.setRecordGroup( screen.group )
		model.setFields( fields )
		model.setFieldsOrder( [x['name'] for x in header] )
		model.setColors( colors )
		model.setReadOnly( not attrs.get('editable', False) )
		view.setReadOnly( not attrs.get('editable', False) )

		if attrs.get('editable', False) == 'top':
			view.setAddOnTop( True )

		if view.isReadOnly():
			model.setShowBackgroundColor( False )
		else:
			model.setShowBackgroundColor( True )

		# Here we use a trick to avoid double data loading.
		# If we don't disallow record loading, records would be loaded twice
		# once, in "view.setModel( model )" and another one when Screen loads
		# view.setViewSettings(). What we do here is disallow record loading,
		# run setModel(), load settings and finally allow record loading again.
		# This optimizes Tree View loading times.
		screen.group.setAllowRecordLoading( False )
		view.setModel( model )

		for column in range( len(columns)):
			current = columns[column]
			if view._widgetType in ('tree','table'):
				view.widget.setColumnWidth( column, current['width'] )
			if not current['visible']:
				view.widget.hideColumn( column )

			delegate = FieldDelegateFactory.create( current['type'], view.widget, current['attributes'] )
			view.widget.setItemDelegateForColumn( column, delegate )

		view.setViewSettings( ViewSettings.load( view.id ) )
		screen.group.setAllowRecordLoading( True )

		return view

# vim:noexpandtab:
