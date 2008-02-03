##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: parser.py 4776 2006-12-05 13:21:09Z ced $
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

from widget.view.abstractparser import *

import time

from widget.view.form.many2one import dialog as M2ODialog
from modules.gui.window.win_search import win_search
from widget.model import treemodel

from tree import *
from PyQt4.uic import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from common import common
from common.numeric import *
from common.calendar import *



class TreeParser(AbstractParser):
	def create(self, parent, model, rootNode, fields, toolbar):
		self.screen = parent
		view = ViewTree( parent, fields )
		
		view.widget.setSortingEnabled(True)
		view.widget.setAlternatingRowColors( True )
		view.widget.setRootIsDecorated( False )

		attrs = common.node_attributes(rootNode)
 		on_write = attrs.get('on_write', '')

		if not view.title:
 			view.title = attrs.get('string', 'Unknown')

		colors = []
		for color_spec in attrs.get('colors', '').split(';'):
			if color_spec:
				colour, test = color_spec.split(':')
				colors.append( ( colour, str(test) ) )

		header = []
		columns = []
		for node in rootNode.childNodes:
			node_attrs = common.node_attributes(node)
 			if node.localName == 'field':
				fname = node_attrs['name']
				twidth = {
					'integer': 60,
					'float': 80,
					'date': 70,
					'datetime': 120,
					'selection': 90,
					'char': 100,
					'one2many': 50,
				}

				if 'readonly' in node_attrs:
					fields[fname]['readonly'] = bool(int(node_attrs['readonly']))
				if 'required' in node_attrs:
					fields[fname]['required'] = bool(int(node_attrs['required']))

				node_attrs.update(fields[fname])

				if 'width' in fields[fname]:
					width = int(fields[fname]['width'])
				else:
					width = twidth.get(fields[fname]['type'], 200)
				header.append( { 'name': fname, 'type': fields[fname]['type'], 'string': fields[fname].get('string', '') })
				columns.append( { 'width': width , 'type': fields[fname]['type'], 'attributes':node_attrs } )

		model = treemodel.TreeModel( view )
		model.setMode( treemodel.TreeModel.ListMode )
		model.setModelGroup( self.screen.models )
		model.setFields( fields )
		model.setFieldsOrder( [x['name'] for x in header] )
		model.setColors( colors )
		model.setReadOnly( not attrs.get('editable', False) )
		view.setReadOnly( not attrs.get('editable', False) )
		#model.setReadOnly( False )

		if view.isReadOnly():
			model.setShowBackgroundColor( False )
		else:
			model.setShowBackgroundColor( True )
		view.setModel( model )

		for column in range( len(columns)):
			current = columns[column]
			view.widget.setColumnWidth( column, current['width'] )
			delegate = StandardDelegate( current['type'], current['attributes'], view.widget )
			view.widget.setItemDelegateForColumn( column, delegate )
		return view, on_write

from widget.view.form import calendar
from widget.view.form import float
from widget.view.form import integer
from widget.view.form import char
from widget.view.form import checkbox
from widget.view.form import reference
from widget.view.form import binary
from widget.view.form import textbox
from widget.view.form import richtext
from widget.view.form import many2many
from widget.view.form import many2one
from widget.view.form import selection
from widget.view.form import one2many
from widget.view.form import url
from widget.view.form import image


widgets_type = {
	'date': calendar.DateFormWidget,
	'time': calendar.TimeFormWidget,
	'datetime': calendar.DateTimeFormWidget,
	'float': float.FloatFormWidget,
	'integer': integer.IntegerFormWidget,
	'selection': selection.SelectionFormWidget,
	'char': char.CharFormWidget,
	'boolean': checkbox.CheckBoxFormWidget,
	'reference': reference.reference,
	'binary': binary.BinaryFormWidget,
	'text': textbox.TextBoxFormWidget,
	'text_tag': richtext.RichTextFormWidget,
	'one2many': one2many.OneToManyFormWidget,
	'one2many_form': one2many.OneToManyFormWidget,
	'one2many_list': one2many.OneToManyFormWidget,
	'many2many': many2many.many2many,
	'many2one': many2one.many2one,
	'image' : image.ImageFormWidget,
	'url' : url.UrlFormWidget,
	'email' : url.EMailFormWidget,
	'callto' : url.CallToFormWidget,
	'sip' : url.SipFormWidget,
}

class StandardDelegate( QItemDelegate ):
	def __init__( self, type, attributes, parent=None):
		QItemDelegate.__init__( self, parent )
		self.attributes = attributes
		self.type = type

	def createEditor( self, parent, option, index ):
		return widgets_type[self.type](parent, None, self.attributes)

	def setEditorData( self, editor, index ):
		if not editor:
			return
		# We suppose a TreeModel here
		model = index.model().modelFromIndex( index )
		editor.load( model )
		return

	def setModelData( self, editor, model, index ):
		if editor:
			editor.store()
		
	def updateEditorGeometry(self, editor, option, index ):
		 editor.setGeometry(option.rect)
	
# vim:noexpandtab:
