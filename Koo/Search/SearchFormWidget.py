##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (c) 2011-2012 P. Christeas <xrg@hellug.gr>
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

import sys
import gettext
from lxml import etree
import logging

#from CustomSearchFormWidget import *
#from SearchViewWidget import *
from SearchWidgetFactory import SearchWidgetFactory
from AbstractSearchWidget import AbstractSearchWidget
from Koo.Common import Common
from Koo.Common import Api
from Koo import Rpc

from PyQt4.QtGui import QWidget, QIcon, QLabel, QGridLayout, QMessageBox, \
        QMenu, QVBoxLayout, QInputDialog, QAction, QKeySequence, QShortcut, \
        QGroupBox, QFrame, QSizePolicy, QHBoxLayout, QPushButton
from PyQt4.QtCore import SIGNAL, Qt, QSize
from Koo.Common.Ui import loadUiType

log = logging.getLogger('koo.screen.search')

class SearchFormContainer(QWidget):
        """Search form widget, arranging layout
        
            Items are placed in columns, and then wrap to rows. But columns are
            NOT aligned along rows! This is because in 6.0 forms, items tend to
            have assymetric width.
        """
        MAX_COLUMNS = 8
        def __init__(self, parent):
                QWidget.__init__( self, parent )
                self.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.Minimum)
    
		layout = QVBoxLayout( self )
		#self.layout().setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		# Maximum number of columns
		self.col = self.MAX_COLUMNS
		self.curRow = None
		self.x = 0
		self.y = 0

	def addWidget(self, widget, name=None):
                
		if self.x + 1 > self.col:
                    self.newRow()

                if not self.curRow:
                    self.curRow = QHBoxLayout()
                    #self.curRow.setSpacing( 0 )
                    self.layout().addLayout(self.curRow)
                    
		# Add gridLine attribute to all widgets so we can easily discover
		# in which line they are.
		widget.gridLine = self.y
		if name:
			label = QLabel( name )
			label.gridLine = self.y
			vbox = QVBoxLayout()
			vbox.setSpacing( 0 )
			vbox.setContentsMargins( 0, 0, 0, 0 )
			vbox.addWidget( label, 0 )
			vbox.addWidget( widget )
			
			self.curRow.addLayout( vbox )
		else:
                	self.curRow.addWidget( widget )
		self.x = self.x + 1

        def newRow(self):
            self.y = self.y + 1
            self.x = 0
            if self.curRow:
                self.curRow.addStretch(1)
            self.curRow = None


class SearchFormExpander(SearchFormContainer):
    """ A group box, that acts as an expander for its content
    """
    def __init__(self, title, parent):
        SearchFormContainer.__init__(self, parent)
        self.expandButton = QPushButton(self)
        self.expandButton.setIcon(SearchFormWidget.Images['up'])
        # self.expandButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.expandButton.setCheckable(True)
        self.expandButton.setChecked(True)
        if title:
            self.expandButton.setText(title)
        self.expandButton.setFlat(True)
        self.expandButton.setIconSize(QSize(16,16))
        self.expandButton.setContentsMargins(0,0,0,0)
        self.addWidget(self.expandButton)
        if False and title:
            label = QLabel(title)
            self.addWidget(label)
        self.expandButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.newRow()
        self.connect(self.expandButton, SIGNAL('toggled(bool)'), self._toggled)

    def _toggled(self, on):
        self.expandButton.setIcon(SearchFormWidget.Images[ on and 'up' or 'down'])
        log.debug("Toggled: %r", on)
        for x in self.children():
            if x.isWidgetType() and x.gridLine > 0:
                if on:
                    x.show()
                else:
                    x.hide()
        self.update()
    
class SearchFormParser(object):
	def __init__(self, parent, container, fields, model='', context=None):
		self.fields = fields
		self.container = container
		self.model = model
		self.focusable = None
		self.parent = parent
		self.shortcuts = []
		assert isinstance(parent, SearchFormWidget), parent
		self.title = _('Form')
		self.context = context or {}
		self.epoch = '5.0'

	def parse_form(self, xml_data):
		dom = etree.fromstring(xml_data)
		log.debug("Parsing search view of \"%s\"", dom.tag)
		if dom.tag in ('form', 'tree'):
                    # 5.0-style form, we scan the fields and generate a crude
                    # search view
                    self._parse_50(dom)
                elif dom.tag == 'search':
                    # 6.0 style search view, we fill the container with the elements
                    # as described by the view
                    self.epoch = '6.0'
                    self._parse_60(dom)
                else:
                    log.warning("Cannot generate search view from \"%s\" view", dom.tag)

        def _parse_50(self, dom):
            """ Parse a form view into a search view container
            """
            if dom.get('string'):
                self.title = dom.get('string')

            fieldNames = set()
            for elem in dom:
                attrs = elem.attrib
                if elem.tag == 'field' and (elem.get('select', False) \
                        or self.fields[elem.attrib['name']].get('select', False)):
                    attrs = dict(elem.attrib)
                    name = attrs.pop('name')
                    if name in fieldNames:
                        continue
                    fieldNames.add( name )
                    field = self.fields[name]
                    field.update( attrs )
                    field['model'] = self.model

                    wtype = field.get('widget',field['type'])
                    widget = SearchWidgetFactory.create( wtype, name, self.container, field)
                    if not widget:
                        continue
                    self.parent.widgets[str(name)] = widget
                    if 'string' in attrs:
                        label = attrs['string']+':'
                    else:
                        label = None
                    self.container.addWidget(widget, label )
                    if not self.focusable:
                        self.focusable = widget

                elif elem.tag == 'shortcut':
                    if not 'key' in attrs:
                        return
                    if not 'goto' in attrs:
                        return
                    #just insert the pairs into some list.
                    self.shortcuts.append( (attrs['key'],attrs['goto']) )

        def _parse_60(self, dom):
            if dom.get('string'):
                self.title = dom.get('string')
            
            for node in dom:
                if node.get('invisible', False):
                    if eval(node.get('invisible'), {'context': self.context}): # FIXME
                        continue
                self._parse_60node(node, self.container)
            
        def _parse_60node(self, node, container):
            attrs = node.attrib
            if node.tag =='field':
                field_name = str(attrs['name'])
                field = self.fields[field_name]
                wtype = attrs.get('widget', field['type'])
                field.update(attrs)
                field['model'] = self.model
                
                widget = SearchWidgetFactory.create( wtype, field_name, container, field)
                if widget:
                    self.parent.widgets[field_name] = widget
                    if not self.focusable:
                        self.focusable = widget

                if 'string' in field:
                    label = field['string']+':'
                else:
                    label = None
                if len(node):
                    # Supplement the widget with more tricks
                    gwidget = SearchFormContainer(container)
                    if widget:
                        gwidget.addWidget(widget)
                    widget = gwidget # and then replace this one
                    
                    for subnode in node:
                        if subnode.get('invisible', False):
                            if eval(subnode.get('invisible'), {'context': self.context}): # FIXME
                                continue
                        self._parse_60node(subnode, widget)

                wid = container.addWidget(widget,label)

            elif node.tag == 'shortcut':
                if not 'key' in attrs:
                    return
                if not 'goto' in attrs:
                    return
                #just insert the pairs into some list.
                self.shortcuts.append( (attrs['key'],attrs['goto']) )

            elif node.tag=='newline':
                container.newRow()

            elif node.tag == 'separator':
                caption = attrs.get( 'string', )
                layout = False
                if caption:
                    separator = QWidget( container )
                    # separator.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                    label = QLabel( separator )
                    label.setText( caption )
                    font = label.font()
                    font.setBold( True )
                    label.setFont( font )
                    line = QFrame( separator )
                    line.setFrameShadow( QFrame.Plain )
                    if attrs.get('orientation') == 'vertical':
                            line.setFrameShape( QFrame.VLine )
                            line.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Expanding )
                            layout = QHBoxLayout( separator )
                    else:
                            line.setFrameShape( QFrame.HLine )
                            line.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
                            layout = QVBoxLayout( separator )
                    #layout.setAlignment( Qt.AlignTop )
                    #layout.setContentsMargins( 0, 0, 0, 0 )
                    layout.setSpacing( 0 )
                    layout.addWidget( label )
                    layout.addWidget( line )
                else:
                    separator = QFrame(container)
                    separator.setFrameShadow( QFrame.Raised )
                    if attrs.get('orientation') == 'vertical':
                        separator.setFrameShape( QFrame.VLine )
                        separator.setSizePolicy( QSizePolicy.Fixed, QSizePolicy.Expanding )
                    else:
                        separator.setFrameShape( QFrame.HLine )
                        separator.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Fixed )
                
                #self.view.addStateWidget( separator, attrs.get('attrs'), attrs.get('states') )
                container.addWidget(separator)

            elif node.tag == 'group':
                
                
                if attrs.get('expand', False):
                    widget = SearchFormExpander(attrs.get('string', None), container)
                    if 'col' in attrs:
                        widget.col = attrs['col']
                    expand = attrs['expand']
                    if isinstance(expand, basestring):
                        # It could be an expression, evaluate it
                        expand = eval(attrs['expand'],
                                        {'context': self.context})
                    widget._toggled(bool(expand))
                else:
                    widget = SearchFormContainer( container)
                    if attrs.get('string', False):
                        widget.addWidget(QLabel(attrs['string']))
                        widget.newRow()
                    if 'col' in attrs:
                        widget.col = attrs['col']
                
                for subnode in node:
                    if subnode.get('invisible', False):
                        if eval(subnode.get('invisible'), {'context': self.context}):
                            continue
                    self._parse_60node(subnode, widget)
                widget.newRow() # this will add a final spacer, thus left-align
                if attrs.get('expand', False):
                    widget.expandButton.setChecked(False)
                #self.view.addStateWidget( widget, attrs.get('attrs'), attrs.get('states') )
                container.addWidget( widget )

            elif node.tag == 'filter':
                name = attrs.get('string', 'filter-%s' % hex(id(node)))
                widget = SearchWidgetFactory.create('filter', name, container, attrs)
                self.parent.widgets[name] = widget
                container.addWidget(widget)

            else:
                log.info("Ignoring a \"%s\" element in search form", node.tag)
                return
            # stop here


(SearchFormWidgetUi, SearchFormWidgetBase) = loadUiType( Common.uiPath('searchform.ui') )

## @brief This class provides a form with the fields to search given a model.
#
# This class will emit the 'search()' signal each time the user pushes the 'search' button.
# Then you can use the 'value()' function to obtain a domain-like list.
class SearchFormWidget(AbstractSearchWidget, SearchFormWidgetUi):
	## @brief Constructs a new SearchFormWidget.
	Images = {}
	def __init__(self, parent=None):
		AbstractSearchWidget.__init__(self, '', parent)
		SearchFormWidgetUi.__init__(self)
		self.setupUi( self )
		
		self.model = None
		self.widgets = {}
		self.name = ''
		self.focusable = True
		self.expanded = True
		self._loaded = False
		self.shortcuts = []
		self._storedFilters = {}

		self.pushExpander.setEnabled( False )
		self.pushClear.setEnabled( False )
		self.pushSearch.setEnabled( False )
		self.toggleView()

                # Load the images, once
                if not self.Images:
                    self.Images.update(up=QIcon(':/images/up.png'),
                            down=QIcon(':/images/down.png'),
                            save=QIcon( ':/images/save.png' ),
                            manage=QIcon( ':/images/administration.png'))
		# Fill in filters menu
		self.actionSave = QAction(self)
		self.actionSave.setText( _('&Save Current Filter') )
		self.actionSave.setIcon( self.Images['save'] )

		self.actionManage = QAction(self)
		self.actionManage.setText( _('&Manage Filters') )
		self.actionManage.setIcon( self.Images['manage'] )

		self.filtersMenu = QMenu( self )
		self.filtersMenu.addAction( self.actionSave )
		self.filtersMenu.addAction( self.actionManage )
		self.pushSave.setMenu( self.filtersMenu )
		self.pushSave.setDefaultAction( self.actionSave )

		# Hide Save button and filters which will be shown if needed in load() method
		self.pushSave.hide()
		self.uiStoredFilters.hide()

		self.connect( self.pushExpander, SIGNAL('clicked()'), self.toggleExpansion )
		self.connect( self.pushClear, SIGNAL('clicked()'), self.clear )
		self.connect( self.pushSearch, SIGNAL('clicked()'), self.search )
		self.connect( self.pushSwitchView, SIGNAL('clicked()'), self.toggleView )
		self.connect( self.actionSave, SIGNAL('triggered()'), self.save )
		self.connect( self.actionManage, SIGNAL('triggered()'), self.manage )
		self.connect( self.uiStoredFilters, SIGNAL('currentIndexChanged(int)'), self.setStoredFilter )

	def setStoredFilter(self, index):
		if index >= 0:
			id = self.uiStoredFilters.itemData( index ).toInt()[0]
			if id:
				storedDomain = eval( self._storedFilters[id]['domain'] )
			else:
				storedDomain = []
			self.uiCustomContainer.setValue( storedDomain )
		else:
			self.uiCustomContainer.setValue( [] )

	## @brief Returns True if it's been already loaded. That is: setup has been called.
	def isLoaded(self):
		return self._loaded

	## @brief Returns True if it has no widgets.
	def isEmpty(self):
		if len(self.widgets): return False
		else:
			return True

	# @brief Manage stored filters
	def manage(self):
		Api.instance.executeAction({
			'name': _('Manage Filters'),
			'res_model': 'ir.filters',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'domain': "[('model_id','=','%s'),('user_id','=',%s)]" % (self.model, Rpc.session.get_uid())
		}, data={}, context=Rpc.session.context)

	# @brief Store current search
	def save(self):
		name, ok = QInputDialog.getText(self, _('Save Filter'), _('What is the name of this filter?'))
		if not ok or not name:
			return
		Rpc.RpcProxy('ir.filters').create_or_replace({
			'name': unicode(name), 
			'user_id': Rpc.session.get_uid(),
			'model_id': self.model,
			'domain': str(self.value()),
			'context': str(Rpc.session.context),
		}, Rpc.session.context)
		self.load()

	def load(self):
		try:
                        # FIXME search_read
			ids = Rpc.RpcProxy('ir.filters').search([
				('user_id','=',Rpc.session.get_uid()),
				('model_id','=',self.model)
			], 0, False, False, Rpc.session.context)
		except Rpc.RpcException, e:
			# If server version is 5.0 and koo module is not installed ir.filters will not be
			# available
			return
			
		# Show filter-related widgets
		self.pushSave.show()
		self.uiStoredFilters.show()

		records = Rpc.session.execute('/object', 'execute', 'ir.filters', 'read', ids, [], Rpc.session.context)
		self.uiStoredFilters.clear()
		self.uiStoredFilters.addItem( '' )
		for record in records:
			self.uiStoredFilters.addItem( record['name'], record['id'] )
			self._storedFilters[ record['id'] ] = record

	## @brief Initializes the widget with the appropiate widgets to search.
	#
	# Needed fields include XML view (usually 'form'), fields dictionary with information
	# such as names and types, and the model parameter.
	def setup(self, xml, fields, model, domain, ):
		# We allow one setup call only
		if self._loaded:
			return

		self._loaded = True
		self.pushExpander.setEnabled( True )
		self.pushClear.setEnabled( True )
		self.pushSearch.setEnabled( True )

                parser = SearchFormParser(self, self.uiSimpleContainer, fields, model)
                #  context from screen or model ? FIXME
		self.model = model

		parser.parse_form(xml)
		log.debug("Len of widgets: %d %r", len(self.widgets), self.widgets.keys())
		for widget in self.widgets.values():
			self.connect( widget, SIGNAL('keyDownPressed()'), self, SIGNAL('keyDownPressed()') )

		for x in domain:
			if len(x) >= 2 and x[0] in self.widgets and x[1] == '=':
				self.widgets[ x[0] ].setEnabled( False )

		for skey, sgoto in parser.shortcuts:
			# print "Trying to associate %s to widget %s at search form." % (skey, sgoto)
			if not sgoto in self.widgets:
				log.warning("Cannot locate widget %s for shortcut.", sgoto)
				continue
			scut = QShortcut(QKeySequence(skey),self)
			self.widgets[sgoto].connect(scut,SIGNAL('activated()'),self.widgets[sgoto].setFocus)
			self.shortcuts.append(scut)
		
                self.name = parser.title
                self.focusable = parser.focusable

		# Don't show expander button unless there are widgets in the
		# second row
		self.pushExpander.hide()
		if parser.epoch < '6.0':
                    for x in self.widgets.values():
			if x.gridLine > 0:
				self.pushExpander.show()
				break

                    self.expanded = True
                    self.toggleExpansion()
                else:
                    self.pushExpander = None

		self.uiCustomContainer.setup( fields, domain )

		#self.uiSearchView.setup( xml, fields, model, domain )
		self.load()

	def keyPressEvent(self, event):
                # FIXME no better way?
		if event.key() in ( Qt.Key_Return, Qt.Key_Enter ):
			self.search()

	def search(self):
		if self.isCustomSearch():
			# Do not emit the signal if the server raises an exception with the search
			# which unfortunately can happen in some cases such as some searches with properties.
			# (ie. [('property_product_pricelist.name','ilike','a')])
			value = self.value()
			proxy = Rpc.RpcProxy( self.model,)
			try:
				proxy.search( value, 0, False, False, Rpc.session.context )
			except Rpc.RpcException, e:
                                # FIXME: remove all that:
				number = 0
				print "exception", e
				for item in value:
					if not isinstance(item, tuple):
						continue

					valid = True
					try:
						self.uiCustomContainer.setItemValid # FIXME
						proxy.search( [item], 0, False, False, Rpc.session.context )
					except Rpc.RpcException, e:
						valid = False

					self.uiCustomContainer.setItemValid(number, valid)
					number += 1

				QMessageBox.warning(self, _('Search Error'), _('Some items of custom search cannot be used. Please, change those in red and try again.'))
				return

			self.uiCustomContainer.setAllItemsValid(True)

		self.emit( SIGNAL('search()') )

	## @brief Shows Search and Clear buttons.
	def showButtons(self):
		self.pushClear.setVisible( True )
		self.pushSearch.setVisible( True )

	## @brief Hides Search and Clear buttons.
	def hideButtons(self):
		self.pushClear.setVisible( False )
		self.pushSearch.setVisible( False )

	def toggleExpansion(self):
                if not self.pushExpander:
                    return
		self.uiSimpleContainer.layout()
		
		childs = self.uiSimpleContainer.children()
		for x in childs:
			if x.isWidgetType() and x.gridLine > 0:
				if self.expanded:
					x.hide()
				else:
					x.show()
		self.expanded = not self.expanded
		if self.expanded:
			self.pushExpander.setIcon( self.Images['up'] )
		else:
			self.pushExpander.setIcon( self.Images['down'] )

	def toggleView(self):
		if self.pushSwitchView.isChecked():
			self.uiSearchView.hide()
			self.uiSimpleContainer.hide()
			if self.pushExpander:
                            self.pushExpander.hide()
			self.uiCustomContainer.show()
		else:
			self.uiSearchView.hide()
			self.uiSimpleContainer.show()
			if self.pushExpander:
                            self.pushExpander.show()
			self.uiCustomContainer.hide()

	def setFocus(self):
		if self.focusable:
			self.focusable.setFocus()
		else:
			QWidget.setFocus(self)

	## @brief Clears all search fields.
	#
	# Calling 'value()' after this function should return an empty list.
	def clear(self):
		if self.pushSwitchView.isChecked():
			return self.uiCustomContainer.clear()

		for x in self.widgets.values():
			x.clear()

	## @brief Returns a domain-like list for the current search parameters.
	#
	# Note you can optionally give a 'domain' parameter which will be added to
	# the filters the widget will return.
	def value(self, domain=None):
                if domain is None:
                    domain = []
		index = self.uiStoredFilters.currentIndex()
		if index > 0:
			id = self.uiStoredFilters.itemData( index ).toInt()[0]
			storedDomain = eval( self._storedFilters[id]['domain'] )
			domain = domain + storedDomain

		if self.pushSwitchView.isChecked():
			return self.uiCustomContainer.value( domain )

		res = []
		for x in self.widgets:
			res += self.widgets[x].value()
		v_keys = [x[0] for x in res]
		for f in domain:
			if f[0] not in v_keys:
				res.append(f)
                log.debug("value(): %r", res)
		return res

	def isCustomSearch(self):
		return self.pushSwitchView.isChecked()

	## @brief Allows setting filter values for all fields in the form.
	#
	# 'val' parameter should be a dictionary with field names as keys and
	# field values as values. Example:
	#
	# form.setValue({
	#	'name': 'enterprise',
	#	'income': 24
	# })
	def setValue(self, val):
		for x in val:
			if x in self.widgets:
				self.widgets[x].value = val[x]

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
