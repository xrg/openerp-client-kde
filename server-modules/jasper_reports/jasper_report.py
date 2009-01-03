##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
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

import os
import base64
from xml.dom.minidom import getDOMImplementation
import report
import pooler
import osv

class report_jasper(report.interface.report_int):
	def __init__(self, name, model):
		super(report_jasper, self).__init__(name)
		self.model = model

	def create(self, cr, uid, ids, data, context):
		self.generate_xml( cr, uid, ids, data['model'], context)
		self.generate_xml( cr, uid, [9], 'account.invoice', context)
		os.spawnlp(os.P_WAIT, '/home/albert/d/koo/server-modules/jasper_reports/java/create-report.sh', '/home/albert/d/koo/server-modules/jasper_reports/java/create-report.sh', '--compile', 'invoice', '/tmp/jasper.xml', '/tmp/output.pdf' )
		print "OutpuT"
		f = open('/tmp/output.pdf', 'rb')
		data = f.read()
		f.close()
		return ( data, 'pdf' )

	def generate_xml(self, cr, uid, ids, model, context):
		pool = pooler.get_pool( cr.dbname )
		document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = document.documentElement

		for record in pool.get(model).browse(cr, uid, ids, context):
			recordNode = document.createElement('record')
			topNode.appendChild( recordNode )
			(fields, fieldNames) = self.fields(pool, model)
			self.generate_record( pool, record, recordNode, document, fields, fieldNames, 2 )
				
		f = open('/tmp/jasper.xml', 'wb+')
		f.write( topNode.toxml() )
		f.close()

	def generate_record(self, pool, record, recordNode, document, fields, fieldNames, depth):
		for field in fieldNames:
			fieldNode = document.createElement(field)
			recordNode.appendChild( fieldNode )
			try:
				value = record.__getattr__(field)
			except:
				print "Exception: ", field

			if isinstance(value, osv.orm.browse_record):
				if depth <= 1:
					continue
				modelName = value._table._name
				(fields, fieldNames) = self.fields(pool, modelName)
				self.generate_record(pool, value, fieldNode, document, fields, fieldNames, depth-1)
				continue

			if isinstance(value, osv.orm.browse_record_list):
				if depth <= 1:
					continue
				if not value:
					continue
				modelName = value[0]._table._name
				(fields, fieldNames) = self.fields(pool, modelName)
				for val in value:
					self.generate_record(pool, val, fieldNode, document, fields, fieldNames, depth-1)
				value = None
				continue

			if value == False:
				value = ''
			elif isinstance(value, unicode):
				value = value.encode('ascii', 'ignore')
			elif not isinstance(value, str):
				value = str(value)

			valueNode = document.createTextNode( value )
			fieldNode.appendChild( valueNode )
		
	def fields(self, pool, model):
		fields = pool.get(model)._columns
		fieldNames = pool.get(model)._columns.keys()
		fieldNames.sort()
		return (fields, fieldNames)

report_jasper( 'report.' + 'res.partner.jaspertest', 'res.partner' ) 
