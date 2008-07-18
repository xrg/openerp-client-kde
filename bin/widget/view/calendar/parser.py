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

from widget.model import treemodel
from widget.view.abstractparser import *
from widget.view.form.abstractformwidget import *
from calendar import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class CalendarParser( AbstractParser ):

	def create(self, parent, model, rootNode, fields):
		self.screen = parent
		view = ViewCalendar( parent )

		attrs = common.node_attributes(rootNode)
 		on_write = attrs.get('on_write', '')

		if not view.title:
 			view.title = attrs.get('string', 'Unknown')

		header = [ attrs['date_start'] ]
		for node in rootNode.childNodes:
			node_attrs = common.node_attributes(node)
 			if node.localName == 'field':
				header.append( node_attrs['name'] )

		#<calendar string="Tasks" date_start="date_start" date_delay="planned_hours" color="user_id">
		#	<field name="name"/>
		#	<field name="project_id"/>
		#</calendar>

		model = treemodel.TreeModel( view )
		model.setMode( treemodel.TreeModel.ListMode )
		model.setModelGroup( self.screen.models )
		model.setFields( fields )
		model.setFieldsOrder( header )
		model.setReadOnly( not attrs.get('editable', False) )
		model.setShowBackgroundColor( True )

		view.setReadOnly( not attrs.get('editable', False) )
		view.setModel( model )
		view.setModelDateColumn( 0 )
		view.setModelTitleColumn( 1 )
		return view, on_write

# vim:noexpandtab:

