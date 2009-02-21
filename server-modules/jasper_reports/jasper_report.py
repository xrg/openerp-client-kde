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
import glob
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
import netsvc

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
		self.temporaryFiles = []
		self.imageFiles = {}

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
		self.temporaryFiles.append( inputFile )
		self.temporaryFiles.append( outputFile )

		# If the language used is xpath create the xmlFile in inputFile.
		if self.reportProperties['language'] == 'xpath':
			if self.data.get('records',False):
				self.generate_xml_from_records( inputFile )
			else:
				self.generate_xml( inputFile )
		# Call the external java application that will generate the PDF file in outputFile
		self.createReport( inputFile, outputFile )

		# Read data from the generated file and return it
		f = open( outputFile, 'rb')
		data = f.read()
		f.close()

		# Remove all temporary files created during the report
		for file in self.temporaryFiles:
			os.unlink( file )
		self.temporaryFiles = []
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
	def userName(self):
		if os.name == 'nt':
			import win32api
			return win32api.GetUserName()
		else:
			import pwd
			return pwd.getpwuid(os.getuid())[0]

	def createReport( self, inputFile, outputFile ):
		host = tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] or '5432'
		dbname = self.cr.dbname
		user = tools.config['db_user'] or self.userName()
		password = tools.config['db_password'] or ''
		dsn= 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )

		idss=""
		for id in self.ids:
			idss += ' %s'%id

		jrxmlFile = os.path.join( self.addonsPath(), self.report )
		jasperFile = os.path.join( self.addonsPath(), self.report[:-6] + '.jasper' )
		self.compileReport( jrxmlFile, jasperFile )
		self.executeReport( jasperFile, inputFile, outputFile, dsn, user, password, 'ids:%s;' % idss )

	def compileReport(self, inputFile, outputFile):
		# Compile report only when the date of .jasper file is older than the one of the .jrxml file
		if os.path.exists(outputFile):
			inputDate = os.stat(inputFile).st_mtime
			outputDate = os.stat(outputFile).st_mtime
			if outputDate > inputDate:
				return
		
		env = {}
		env.update( os.environ )
		env['CLASSPATH'] = os.path.join( self.path(), 'java:' ) + ':'.join( glob.glob( os.path.join( self.path(), 'java/lib/*.jar' ) ) ) 
		os.spawnlpe(os.P_WAIT, 'java', 'java', 'ReportCompiler', inputFile, outputFile, env)

	def executeReport(self, inputFile, xmlFile, outputFile, dsn, user, password,  params):
		env = {}
		env.update( os.environ )
		env['CLASSPATH'] = os.path.join( self.path(), 'java:' ) + ':'.join( glob.glob( os.path.join( self.path(), 'java/lib/*.jar' ) ) ) 
		os.spawnlpe(os.P_WAIT, 'java', 'java', 'ReportCreator', inputFile, xmlFile, outputFile, dsn, user, password, params, env)

	# XML file generation using a list of dictionaries provided by the parser function.
	def generate_xml_from_records(self, fileName):
		# Once all records have been calculated, create the XML structure itself
		self.document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = self.document.documentElement
		for record in self.data['records']:
			recordNode = self.document.createElement('record')
			topNode.appendChild( recordNode )
			for field, value in record.iteritems():
				fieldNode = self.document.createElement( field )
				recordNode.appendChild( fieldNode )
				# The rest of field types must be converted into str
				if value == False:
					value = ''
				elif not isinstance(value, str):
					value = str(value)
				valueNode = self.document.createTextNode( value )
				fieldNode.appendChild( valueNode )
		# Once created, the only missing step is to store the XML into a file
		f = open( fileName, 'wb+')
		topNode.writexml( f )
		f.close()

	# XML file generation works as follows:
	# By default (if no OPENERP_RELATIONS property exists in the report) a record will be created
	# for each model id we've been asked to show. If there are any elements in the OPENERP_RELATIONS
	# list, they will imply a LEFT JOIN like behaviour on the rows to be shown.
	def generate_xml(self, fileName):
		self.allRecords = []
		relations = self.reportProperties['relations']
		# The following loop generates one entry to allRecords list for each record
		# that will be created. If there are any relations it acts like a
		# LEFT JOIN against the main model/table.
		for record in self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context):
			self.allRecords += self.generate_ids( record, relations, '', [ { 'root': record } ] )

		# Once all records have been calculated, create the XML structure itself
		self.document = getDOMImplementation().createDocument(None, 'data', None)
		topNode = self.document.documentElement
		for records in self.allRecords:
			recordNode = self.document.createElement('record')
			topNode.appendChild( recordNode )
			self.generate_record( records['root'], records, recordNode, '', self.reportProperties['fields'] )

		# Once created, the only missing step is to store the XML into a file
		f = open( fileName, 'wb+')
		topNode.writexml( f )
		f.close()

	def generate_ids(self, record, relations, path, currentRecords):
		unrepeated = set( [field.partition('/')[0] for field in relations] )
		for relation in unrepeated:
			root = relation.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
			if root == 'Attachments':
				ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('res_model','=',record._table_name),('res_id','=',record.id)])
				value = self.pool.get('ir.attachment').browse(self.cr, self.uid, ids, self.context)
			else:
				try:
					value = record.__getattr__(root)
				except:
					print "Field '%s' does not exist in model '%s'." % (root, self.model)
					continue

				if isinstance(value, osv.orm.browse_record):
					relations2 = [ f.partition('/')[2] for f in relations if f.partition('/')[0] == root and f.partition('/')[2] ]
					return self.generate_ids( value, relations2, currentPath, currentRecords )

				if not isinstance(value, osv.orm.browse_record_list):
					print "Field '%s' in model '%s' is not a relation." % (root, self.model)
					return currentRecords

			# Only join if there are any records because it's a LEFT JOIN
			# If we wanted an INNER JOIN we wouldn't check for "value" and
			# return an empty currentRecords
			if value:
				# Only 
				newRecords = []
				for v in value:
					currentNewRecords = []
					for id in currentRecords:
						new = id.copy()
						new[currentPath] = v
						currentNewRecords.append( new )
					relations2 = [ f.partition('/')[2] for f in relations if f.partition('/')[0] == root and f.partition('/')[2] ]
					newRecords += self.generate_ids( v, relations2, currentPath, currentNewRecords )

				currentRecords = newRecords
		return currentRecords

	def generate_record(self, record, records, recordNode, path, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once by using a set.
		unrepeated = set( [field.partition('/')[0] for field in fields] )
		for field in unrepeated:
			root = field.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
			fieldNode = self.document.createElement( root )
			recordNode.appendChild( fieldNode )
			if root == 'Attachments':
				ids = self.pool.get('ir.attachment').search(self.cr, self.uid, [('res_model','=',record._table_name),('res_id','=',record.id)])
				value = self.pool.get('ir.attachment').browse(self.cr, self.uid, ids)
			else:
				try:
					value = record.__getattr__(root)
				except:
					value = None
					print "Field '%s' does not exist in model" % root

			# Check if it's a many2one
			if isinstance(value, osv.orm.browse_record):
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generate_record(value, records, fieldNode, currentPath, fields2)
				continue

			# Check if it's a one2many or many2many
			if isinstance(value, osv.orm.browse_record_list):
				if not value:
					continue
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if currentPath in records:
					self.generate_record(records[currentPath], records, fieldNode, currentPath, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generate_record(value[0], records, fieldNode, currentPath, fields2)
				continue

			# The rest of field types must be converted into str
			if field == 'id':
				# Check for field 'id' because we can't find it's type in _columns
				value = str(value)
			elif value == False:
				value = ''
			elif record._table._columns[field]._type == 'date':
				value = '%s 00:00:00' % str(value) 
			elif record._table._columns[field]._type == 'binary':
				imageId = (record.id, field)
				if imageId in self.imageFiles:
					fileName = self.imageFiles[ imageId ]
				else:
					fd, fileName = tempfile.mkstemp()
					f = open( fileName, 'wb+' )
					f.write( base64.decodestring( value ) )
					f.close()
					self.temporaryFiles.append( fileName )
					self.imageFiles[ imageId ] = fileName
				value = fileName
			elif not isinstance(value, str):
				value = str(value)

			valueNode = self.document.createTextNode( value )
			fieldNode.appendChild( valueNode )


class report_jasper(report.interface.report_int):
	def __init__(self, name, model, parser=None ):
		# Remove report name from list of services if it already
		# exists to avoid report_int's assert. We want to keep the 
		# automatic registration at login, but at the same time we 
		# need modules to be able to use a parser for certain reports.
		if name in netsvc._service:
			del netsvc._service[name]
		super(report_jasper, self).__init__(name)
		self.model = model
		self.parser = parser

	def create(self, cr, uid, ids, data, context):
		name = self.name
		if self.parser:
			d = self.parser( cr, uid, ids, data, context )
			ids = d.get( 'ids', ids )
			name = d.get( 'name', self.name )
			# Use model defined in report_jasper definition. Necesary for menu entries.
			data['model'] = d.get( 'model', self.model )
			data['records'] = d.get( 'records', [] )

		r = Report( name, cr, uid, ids, data, context )
		return ( r.execute(), 'pdf' )



# Ugly hack to avoid developers the need to register reports
import service.security
import pooler

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
				name = 'report.%s' % record['report_name']
				if name in netsvc._service:
					del netsvc._service[name]
				report_jasper( name, record['model'] )
	return uid

service.security.login = new_login

