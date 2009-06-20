#!/usr/bin/python

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


from Koo.Common import Localization
Localization.initializeTranslations()

from Koo import Rpc

from Koo.Model.Group import *
from Koo.Model.KooModel import *

import sys
from PyQt4.QtGui import *

class MenuDialog(QDialog):
	def __init__(self,parent=None):
		QDialog.__init__(self,parent)

		Rpc.session.login( 'http://admin:admin@127.0.0.1:8069', 'nan' )

		#model = 'account.account'
		#visibleFields = ['name', 'code', 'debit', 'credit', 'balance', 'company_currency_id']
		#domain = [('code', '=', '0')]

		model = 'ir.ui.menu'
		visibleFields = ['name']
		extraFields = ['child_id', 'icon']
		domain = [('parent_id','=',False)]

		#model = 'res.partner.address'
		#visibleFields = ['partner_id', 'name', 'zip', 'city', 'country_id']
		#visibleFields = ['street', 'name', 'zip', 'city', 'street2']
		extraFields = []
		domain = []

		self.fields = Rpc.session.execute('/object', 'execute', model, 'fields_get', 
				visibleFields + extraFields  )
		ids = Rpc.session.execute('/object', 'execute', model, 'search', domain)
		import gc
		import sys
		#from muppy import tracker

		self.group = RecordGroup( model, self.fields, ids )
		#mt = tracker.ObjectTracker()
		iterations = 0
		for x in xrange(iterations):
			#print "NUM OBJECTS: ", len(gc.get_objects())
			self.group = RecordGroup( model, self.fields, ids )
			print "GC 0: ", len(gc.get_referrers(self.group))
			#for x in gc.get_referrers(self.group):
			#	print "REF: ", x
			#	print "--------"
			self.group.ensureAllLoaded()
			#print "GC 0: ", len(gc.get_referrers(self.group))
			#print "GC 1: ", sys.getrefcount(self.group)
			#print "COUNT: ", len(self.group.records)
			#for r in self.group.records:
				#r.parent = None
				#r.group = None
				#r.setParent( None )
				#for key, value in r.values.iteritems():
					#import Koo.Model.Field
					#if isinstance(value, Koo.Model.Field.ToManyField):
						#value.parent = None
				#r.values = {}
			##print "COUNT 2: ", len(self.group.fieldObjects)
			#self.group.records = []
			#for f in self.group.fieldObjects:
				#self.group.fieldObjects[f].parent = None
			#self.group.fieldObjects = {}
			#print "NUM OBJECTS: ", len(gc.get_objects())
			#print "GC 1: ", len(gc.get_referrers(self.group))
			#del self.group
			#del f
			#del r
			#del self.group
			if x != iterations - 1:
				self.group.__del__()
			#self.group = None
			gc.collect()
			#mt.print_diff()
			print "NUM OBJECTS: ", len(gc.get_objects())
			#print "----"
			#print "GC: ", gc.get_referrers(self.group)
			print "GC: ", len(gc.get_referrers(self.group))
		print "AFD"

		# Setup Qt Model
		self.model = KooModel( self )
		self.model.setFields( self.fields )
		self.model.setFieldsOrder( visibleFields )
		self.model.setIconForField( 'icon', 'name')
		self.model.setChildrenForField( 'child_id', 'name' )
		self.model.setShowBackgroundColor( False )
		self.model.setRecordGroup( self.group )

		# Create GUI
		layout = QVBoxLayout(self)
		#widget = QTreeView(self)
		widget = QColumnView(self)
		#widget = QListView(self)
		#widget.setViewMode( QListView.IconMode )
		#widget.setGridSize( QSize( 100, 100 ) )
		layout.addWidget(widget)
		layout.setMargin( 0 )
		widget.setModel( self.model )

app = QApplication(sys.argv)
Localization.initializeQtTranslations()

dialog = MenuDialog()

dialog.show()
app.exec_()
