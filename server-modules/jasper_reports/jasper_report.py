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
import xml.xpath
import xml.dom.minidom
import report
import pooler
import osv
import tools
import tempfile 
import codecs
import sql_db

class Report:
	def __init__(self, name, cr, uid, ids, data, context):
		self.name = name
		self.cr = cr
		self.uid = uid
		self.ids = ids
		self.data = data
		self.model = self.data['model']
		self.context = context
		self.pool = pooler.get_pool( self.cr.dbname )
		self.reportPath = None
		self.report = None

	def execute(self):
		fd, outputFile = tempfile.mkstemp()
		fd, inputFile = tempfile.mkstemp()
		# Find out if the report expects an XML or JDBC connection
		reports = self.pool.get( 'ir.actions.report.xml' )
		ids = reports.search(self.cr, self.uid, [('report_name', '=', self.name[7:])], context=self.context)
		self.report = reports.read(self.cr, self.uid, ids[0], ['report_rml'])['report_rml']
		self.reportPath = "%s/%s" % ( self.addonsPath(), self.report )
		self.reportProperties = self.extractReportProperties()
		if self.reportProperties['language'] == 'xpath':
			self.xmlReport( self.ids, inputFile, outputFile )
		else:
			self.createReport( self.ids, inputFile, outputFile )
		f = open( outputFile, 'rb')
		data = f.read()
		f.close()

	def path(self):
		return os.path.abspath(os.path.dirname(__file__))

	def addonsPath(self):
		return os.path.dirname( self.path() )	

	def processRelations(self, ids, relations):
		# relation example: ('line_id', 'LEFT', ('tax_id', 'LEFT'))
		print "Relations: ", relations
		relations = eval( relations )
		print "Relations: ", relations
		fromClause = self.relationTuple( self.model, relations )
		query = "SELECT a.id, b.id FROM %s WHERE a.id IN (%s)" % ( fromClause, ','.join( ids ) )
		print "QUERY: ", query
		return query

	def relationTuple(self, model, relation):
		field = relation[0].strip().lower()
		joinType = relation[1].strip().upper()

		print "RELLEN: ", len(relation)
		print "RELATION: ", relation
		if len(relation) > 2:
			self.relationTuple( relation[3] )
		else:
			relatedModel = model._columns[field]._obj
			relatedTable  = self.pool.get(relatedModel)._table

		if joinType == 'LEFT':
			joinName = 'LEFT JOIN'
		elif joinType == 'INNER':
			joinName = 'INNER JOIN'
		else:
			joinName = joinType

		leftAlias = 'a'
		rightAlias = 'b'
		fullAlias = 'c'

		tables = '%s AS %s %s %s AS %s' % ( model._table, leftAlias, joinName, relatedTable, rightAlias )
		fields = '%s.%s = %s.id' % (leftAlias, field, rightAlias)
		fromClause = '( %s ON (%s)) AS %s' % (tables, fields, fullAlias )
		return fromClause

		
	def extractReportProperties(self):
		# Open report file '....jrxml'
		print "PATH: ", self.reportPath
		f = codecs.open( self.reportPath, 'r', 'utf-8' )
		data = f.read()
		f.close()
		# XML processing
		properties = {
			'language': 'SQL',
			'relations': '',
			'fields': []
		}

		doc = xml.dom.minidom.parseString( data )
		langTags = xml.xpath.Evaluate( '/jasperReport/queryString', doc )
		if langTags:
			properties['language'] = langTags[0].getAttribute('language').lower()
		
		relationTags = xml.xpath.Evaluate( '/jasperReport/parameter[@name="OPENERP_RELATIONS"]/defaultValueExpression', doc )
		if relationTags:
			properties['relations'] = relationTags[0].firstChild.data

		fields = []
		fieldTags = xml.xpath.Evaluate( '/jasperReport/field/fieldDescription', doc )
		for tag in fieldTags:
			properties['fields'].append( tag.firstChild.data )

		return properties
	
	def xmlReport( self, ids, inputFile, outputFile ):
		#if self.reportProperties['relations']:
			#query = self.processRelations( ids, self.reportProperties['relations'] )
		self.generate_xml( ids, inputFile )
		self.createReport( ids, inputFile, outputFile )

	def createReport( self, ids, inputFile, outputFile ):
		host = tools.config['db_host'] and "%s" % tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] and "%s" % tools.config['db_port'] or '5432'
		dbname = "%s" % self.cr.dbname
		user = tools.config['db_user'] and "%s" % tools.config['db_user'] or 'postgres'
		password = tools.config['db_password'] and "%s" % tools.config['db_password'] or 'a'
		maxconn = int(tools.config['db_maxconn']) or 64
		dsn= 'jdbc:postgresql://%s:%s/%s'%(host,port,dbname)

		idss=""
		for id in ids:
			idss += ' %s'%id

		os.spawnlp(os.P_WAIT, self.path() + '/java/create-report.sh', self.path() + '/java/create-report.sh', 
	              '--compile', self.addonsPath(), self.report[:-6], inputFile, outputFile, dsn, user, password, 'ids:%s;' % idss )

	def pathToNode(self, node):
		path = []
		n = node
		while not isinstance(n, xml.dom.minidom.Document):
			path = [ n.tagName ] + path
			n = n.parentNode
		return '/'.join( path )

	def generate_xml(self, ids, fileName):
		self.document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = self.document.documentElement

		for record in self.pool.get(self.model).browse(self.cr, self.uid, ids, self.context):
			recordNode = self.document.createElement('record')
			topNode.appendChild( recordNode )
			#(fields, fieldNames) = self.fields(self.model)
			#self.generate_record_old( record, recordNode, document, fields, fieldNames, 3 )
			self.generate_record( record, recordNode, self.reportProperties['fields'] )
				
		f = open( fileName, 'wb+')
		f.write( topNode.toxml() )
		f.close()

	def generate_record(self, record, recordNode, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once.
		unrepeated = set( [field.partition('/')[0] for field in fields] )
		for field in unrepeated:
			root = field.partition('/')[0]
			fieldNode = self.document.createElement( root )
			recordNode.appendChild( fieldNode )
			try:
				value = record.__getattr__(root)
			except:
				value = None
				print "Field '%s' does not exist in model" % root

			if isinstance(value, osv.orm.browse_record):
				modelName = value._table._name
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generate_record(value, fieldNode, fields2)
				continue
			if isinstance(value, osv.orm.browse_record_list):
				if not value:
					continue
				modelName = value[0]._table._name
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				print "F2: ", fields2
				for val in value:
					self.generate_record(val, fieldNode, fields2)
				continue

			if value == False:
				value = ''
			elif isinstance(value, unicode):
				value = value.encode('ascii', 'ignore')
			elif not isinstance(value, str):
				value = str(value)

			valueNode = self.document.createTextNode( value )
			fieldNode.appendChild( valueNode )

	def generate_record_old(self, record, recordNode, document, fields, fieldNames, depth):
		print "PATH TO NODE. ", self.pathToNode( recordNode )
		for field in fieldNames:
			fieldNode = document.createElement(field)
			#if self.pathToNode( fieldNode ) in self.reportProperties['fields']:
				#print "FIELD %s FOUND!", fieldNode

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
				(fields2, fieldNames2) = self.fields(modelName)
				self.generate_record(value, fieldNode, document, fields2, fieldNames2, depth-1)
				continue

			if isinstance(value, osv.orm.browse_record_list):
				if depth <= 1:
					continue
				if not value:
					continue
				modelName = value[0]._table._name
				(fields2, fieldNames2) = self.fields(modelName)
				for val in value:
					self.generate_record(val, fieldNode, document, fields2, fieldNames2, depth-1)
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
		
	def fields(self, model):
		fields = self.pool.get(model)._columns
		fieldNames = self.pool.get(model)._columns.keys()
		fieldNames.sort()
		return (fields, fieldNames)

class report_jasper(report.interface.report_int):
	def __init__(self, name, model ):
		super(report_jasper, self).__init__(name)
		print "report_jasper:",name,model
		self.model = model

	def create(self, cr, uid, ids, data, context):
		r = Report( self.name, cr, uid, ids, data, context )
		r.execute()
		return ( r.execute(), 'pdf' )



# Ugly hack to avoid developers the need to register reports
import service.security
import pooler
import netsvc

old_login = service.security.login 
def new_login(db, login, password):
	uid = old_login(db, login, password)
	if uid:
		pool = pooler.get_pool(db)
		cr = pooler.get_db(db).cursor()
		ids = pool.get('ir.actions.report.xml').search(cr, uid, [])
		records = pool.get('ir.actions.report.xml').read(cr, uid, ids, ['report_name','report_rml','model'])
		for record in records:
			path = record['report_rml']
			if path and path.endswith('.jrxml'):
				print "REGISTERING REPORT JRXML: ", record['report_name']
				name = 'report.%s' % record['report_name']
				if name in netsvc._service:
					del netsvc._service[name]
				report_jasper( name, record['model'] )
	return uid
service.security.login = new_login

#a = report_jasper( 'report.'+'account_invoice.jaspertest', 'account_invoice' )
#print a.__module__
#print dir( a.__module__ )
