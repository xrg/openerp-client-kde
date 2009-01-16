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
		# Get the report path
		reports = self.pool.get( 'ir.actions.report.xml' )
		ids = reports.search(self.cr, self.uid, [('report_name', '=', self.name[7:])], context=self.context)
		self.report = reports.read(self.cr, self.uid, ids[0], ['report_rml'])['report_rml']
		self.reportPath = "%s/%s" % ( self.addonsPath(), self.report )

		# Get report information from the jrxml file
		self.reportProperties = self.extractReportProperties()

		# Create temporary input (XML) and output (PDF) files 
		fd, inputFile = tempfile.mkstemp()
		fd, outputFile = tempfile.mkstemp()

		# If the language used is xpath create the xmlFile in inputFile.
		if self.reportProperties['language'] == 'xpath':
			self.generate_xml( inputFile )
		# Call the external java application that will generate the PDF file in outputFile
		self.createReport( inputFile, outputFile )

		# Read data from the generated file and return it
		f = open( outputFile, 'rb')
		data = f.read()
		f.close()
		return data

	def path(self):
		return os.path.abspath(os.path.dirname(__file__))

	def addonsPath(self):
		return os.path.dirname( self.path() )

	def extractReportProperties(self):
		# The function will read all relevant information from the jrxml file
		properties = {
			'language': 'SQL',
			'relations': '',
			'fields': []
		}

		doc = xml.dom.minidom.parse( self.reportPath )
		langTags = xml.xpath.Evaluate( '/jasperReport/queryString', doc )
		if langTags:
			properties['language'] = langTags[0].getAttribute('language').lower()
		
		relationTags = xml.xpath.Evaluate( '/jasperReport/property[@name="OPENERP_RELATIONS"]', doc )
		if relationTags and relationTags[0].hasAttribute('value'):
			# Evaluate twice as the first one extracts the "" and returns a plain string.
			# The second one evaluates the string without the "".
			properties['relations'] = eval( relationTags[0].getAttribute('value') )

		fields = []
		fieldTags = xml.xpath.Evaluate( '/jasperReport/field/fieldDescription', doc )
		for tag in fieldTags:
			path = tag.firstChild.data
			# Make the path relative if it isn't already
			if path.startswith('/data/record/'):
				path = path[13:]
			properties['fields'].append( path )

		return properties
	
	def createReport( self, inputFile, outputFile ):
		host = tools.config['db_host'] and "%s" % tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] and "%s" % tools.config['db_port'] or '5432'
		dbname = "%s" % self.cr.dbname
		user = tools.config['db_user'] and "%s" % tools.config['db_user'] or 'postgres'
		password = tools.config['db_password'] and "%s" % tools.config['db_password'] or ''
		dsn= 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )

		idss=""
		for id in self.ids:
			idss += ' %s'%id

		os.spawnlp(os.P_WAIT, self.path() + '/java/create-report.sh', self.path() + '/java/create-report.sh', 
	              self.addonsPath(), self.report[:-6], inputFile, outputFile, dsn, user, password, 'ids:%s;' % idss )

	# XML file generation works as follows:
	# By default (if no OPENERP_RELATIONS property exists in the report) a record will be created
	# for each model id we've been asked to show. If there are any elements in the OPENERP_RELATIONS
	# list, they will imply a LEFT JOIN like behaviour on the rows to be shown.
	def generate_xml(self, fileName):
		self.document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = self.document.documentElement

		# The following loop generates one entry to allRecords list for each record
		# that will be created. If there are any relations it acts like a
		# LEFT JOIN against the main model/table.
		relations = self.reportProperties['relations']
		allRecords = []
		for record in self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context):
			currentRecords = [ { 'root': record } ]
			for relation in relations:
				if isinstance(relation,list):
					continue
				try:
					value = record.__getattr__(relation)
				except:
					print "Field '%s' does not exist in model '%s'." % (relation, self.model)
					continue

				if not isinstance(value, osv.orm.browse_record_list):
					print "Field '%s' in model '%s' is not a list (2many)." % (relation, self.model)
					continue

				newRecords = []
				for v in value:
					for id in currentRecords:
						new = id.copy()
						new[relation] = v
						newRecords.append( new )
				currentRecords = newRecords
			allRecords += currentRecords

		# Once all records have been calculated, create the XML structure itself
		for records in allRecords:
			recordNode = self.document.createElement('record')
			topNode.appendChild( recordNode )
			self.generate_record( records['root'], records, recordNode, self.reportProperties['fields'] )

		# Once created, the only missing step is to store the XML into a file
		f = open( fileName, 'wb+')
		topNode.writexml( f )
		f.close()

	def generate_record(self, record, records, recordNode, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once by using a set.
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
				self.generate_record(value, records, fieldNode, fields2)
				continue

			if isinstance(value, osv.orm.browse_record_list):
				if not value:
					continue
				modelName = value[0]._table._name
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if root in records:
					self.generate_record(records[root], records, fieldNode, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generate_record(value[0], records, fieldNode, fields2)
				continue

			if value == False:
				value = ''
			elif not isinstance(value, str):
				value = str(value)

			valueNode = self.document.createTextNode( value )
			fieldNode.appendChild( valueNode )


class report_jasper(report.interface.report_int):
	def __init__(self, name, model ):
		super(report_jasper, self).__init__(name)
		self.model = model

	def create(self, cr, uid, ids, data, context):
		r = Report( self.name, cr, uid, ids, data, context )
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
