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
import tools

from tempfile import *

import sql_db

class report_jasper(report.interface.report_int):
	def __init__(self, name, model ):
		super(report_jasper, self).__init__(name)
		print "report_jasper:",name,model
		self.model = model
		

	def create(self, cr, uid, ids, data, context):
		f = NamedTemporaryFile()
		fa="/tmp/aaaa"
		if True:
			self.sqlReport(cr,uid,ids,data,context,fa )
		else:
			self.generate_xml( cr, uid, ids, data['model'], context)
			self.generate_xml( cr, uid, ids, 'account.invoice', context)
			os.spawnlp(os.P_WAIT, '/home/angel/work/koo/server-modules/jasper_reports/java/create-report.sh', '/home/angel/work/koo/server-modules/jasper_reports/java/create-report.sh', '--compile', 'invoice2', '/tmp/jasper.xml', '/tmp/output.pdf', )
			print "OutpuT"
		
		f = open( fa, 'rb')
		data = f.read()
		f.close()
		return ( data, 'pdf' )

	def sqlReport( self,cr,uid,ids,data,context, file):
		print "Name:", self.name, "Model:", self.model
 
		host = tools.config['db_host'] and "%s" % tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] and "%s" % tools.config['db_port'] or '5432'
		dbname = "%s" % cr.dbname
		user = tools.config['db_user'] and "%s" % tools.config['db_user'] or 'postgres'
		password = tools.config['db_password'] and "%s" % tools.config['db_password'] or 'a'
		maxconn = int(tools.config['db_maxconn']) or 64
		dsn= 'jdbc:postgresql://%s:%s/%s'%(host,port,dbname)

		print "dsn:",dsn,"ids:",ids,"contexte:",context

		pool = pooler.get_pool( cr.dbname )
		reports = pool.get( 'ir.actions.report.xml' )
		report_xml_ids = reports.search(cr, uid, [('report_name', '=', self.name[7:])], context=context)
		print "IDS:",report_xml_ids
		report_xml = reports.browse(cr, uid, report_xml_ids[0], {})

		print "FILES:", report_xml.report_rml[:-6]


		print file
		idss=""
		for id in ids:
			idss += ' %s'%id

		os.spawnlp(os.P_WAIT, '/home/angel/work/koo/server-modules/jasper_reports/java/create-report.sh', 
			              '/home/angel/work/koo/server-modules/jasper_reports/java/create-report.sh', 
			              '--compile', report_xml.report_rml[:-6], '/tmp/jasper.xml', file, dsn,user,password,'ids:%s;'%idss)
		

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
		#print "fieldName:",fieldNames
		#print "record:",record
		for field in fieldNames:
			fieldNode = document.createElement(field)
			recordNode.appendChild( fieldNode )
			try:
				value = record.__getattr__(field)
			except:
				value=None
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


#a = report_jasper( 'report.'+'account_invoice.jaspertest', 'account_invoice' )
#print a.__module__
#print dir( a.__module__ )
