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
import csv
import copy
import base64
import glob
from xml.dom.minidom import getDOMImplementation
import xml.xpath
import xml.dom.minidom
import report
import pooler
from osv import orm, osv, fields
import tools
import tempfile 
import codecs
import sql_db
import netsvc

from jasper_server import JasperServer

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
		self._languages = []

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
		print "TEMP INPUT: ", inputFile

		import time
		start = time.time()
		# If the language used is xpath create the xmlFile in inputFile.
		if self.reportProperties['language'] == 'xpath':
			if self.data.get('data_source','model') == 'records':
				#self.generate_xml_from_records( inputFile )
				self.generate_csv_from_records( inputFile )
			else:
				#self.generate_xml( inputFile )
				self.generate_csv( inputFile )
		# Call the external java application that will generate the PDF file in outputFile
		self.createReport( inputFile, outputFile )
		end = time.time()
		print "ELAPSED: ", ( end - start ) / 60

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
			'fields': {},
			'fieldNames': []
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

		fields = {}
		fieldTags = xml.xpath.Evaluate( '/jasperReport/field', doc )
		for tag in fieldTags:
			name = tag.getAttribute('name')
			type = tag.getAttribute('class')
			path = tag.getElementsByTagName('fieldDescription')[0].firstChild.data
			# Make the path relative if it isn't already
			if path.startswith('/data/record/'):
				path = path[13:]
			# Remove language specific data from the path so:
			# Empresa-partner_id/Nom-name becomes partner_id/name
			# We need to consider the fact that the name in user's language
			# might not exist, hence the easiest thing to do is split and [-1]
			newPath = []
			for x in path.split('/'):
				newPath.append( x.split('-')[-1] )
			path = '/'.join( newPath )
			properties['fields'][ path ] = {
				'name': name,
				'type': type,
			}
			properties['fieldNames'].append( name )
		return properties

	def userName(self):
		if os.name == 'nt':
			import win32api
			return win32api.GetUserName()
		else:
			import pwd
			return pwd.getpwuid(os.getuid())[0]

	def createReport( self, inputFile, outputFile,  ):
		host = tools.config['db_host'] or 'localhost'
		port = tools.config['db_port'] or '5432'
		dbname = self.cr.dbname
		user = tools.config['db_user'] or self.userName()
		password = tools.config['db_password'] or ''
		dsn= 'jdbc:postgresql://%s:%s/%s' % ( host, port, dbname )

		jrxmlFile = os.path.join( self.addonsPath(), self.report )
		#jasperFile = os.path.join( self.addonsPath(), self.report[:-6] + '.jasper' )
		self.executeReport( jrxmlFile, inputFile, outputFile, dsn, user, password )

	def executeReport(self, jrxmlFile, dataFile, outputFile, dsn, user, password):
		standardDirectory = os.path.join( os.path.abspath(os.path.dirname(__file__)), 'report', '' )
		locale = self.context.get('lang', 'en_US')
		
		connectionParameters = {
			#'xml': dataFile,
			'csv': dataFile,
			'dsn': dsn,
			'user': user,
			'password': password
		}
		parameters = {
			'STANDARD_DIR': standardDirectory,
			'REPORT_LOCALE': locale,
			'IDS': self.ids,
		}
		if 'parameters' in self.data:
			parameters.update( self.data['parameters'] )

		server = JasperServer()
		server.execute( connectionParameters, jrxmlFile, outputFile, parameters )

		
	def executeReport1(self, inputFile, xmlFile, outputFile, dsn, user, password,  params):
		# Note that the STANDARD_DIR parameter is expected to end with a slash (or backslash)
		standardDirectory = os.path.join( os.path.abspath(os.path.dirname(__file__)), 'report', '' )
		env = {}
		env.update( os.environ )
		env['CLASSPATH'] = os.path.join( self.path(), 'java:' ) + ':'.join( glob.glob( os.path.join( self.path(), 'java/lib/*.jar' ) ) ) 
		# Add report file directory to CLASSPATH so bundle (.properties) files can be found
		# by JasperReports.
		env['CLASSPATH'] += ':' + os.path.abspath( os.path.dirname( inputFile ) ) 
		
		locale = self.context.get('lang', 'en_US')
		os.spawnlpe(os.P_WAIT, 'java', 'java', 'ReportCreator', inputFile, xmlFile, outputFile, locale, dsn, user, password, params, standardDirectory, env)


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
				elif isinstance(value, str):
					value = unicode(value, 'utf-8')
				elif not isinstance(value, unicode):
					value = unicode(value)
				valueNode = self.document.createTextNode( value )
				fieldNode.appendChild( valueNode )
		# Once created, the only missing step is to store the XML into a file
		f = codecs.open( fileName, 'wb+', 'utf-8' )
		topNode.writexml( f )
		f.close()

	# CSV file generation using a list of dictionaries provided by the parser function.
	def generate_csv_from_records(self, fileName):
		f = open( fileName, 'wb+' )
		csv.QUOTE_ALL = True
		fieldNames = self.reportProperties['fieldNames']
		# JasperReports CSV reader requires an extra colon at the end of the line.
		writer = csv.DictWriter( f, fieldNames + [''], delimiter=',', quotechar='"' )
		header = {}
		for field in fieldNames + ['']:
			header[ field ] = field
		writer.writerow( header )
		for record in self.data['records']:
			row = {}
			for field in record:
				if field not in self.reportProperties['fields']:
					print "FIELD '%s' NOT FOUND IN REPORT." % field 
					continue
				value = record.get(field, False)
				if value == False:
					value = ''
				elif isinstance(value, unicode):
					value = value.encode('utf-8')
				elif not isinstance(value, str):
					value = str(value)
				row[self.reportProperties['fields'][field]['name']] = value
			writer.writerow( row )
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
			self.generate_record_xml( records['root'], records, recordNode, '', self.reportProperties['fields'] )

		# Once created, the only missing step is to store the XML into a file
		f = codecs.open( fileName, 'wb+', 'utf-8' )
		topNode.writexml( f )
		f.close()

	# CSV file generation works as follows:
	# By default (if no OPENERP_RELATIONS property exists in the report) a record will be created
	# for each model id we've been asked to show. If there are any elements in the OPENERP_RELATIONS
	# list, they will imply a LEFT JOIN like behaviour on the rows to be shown.
	def generate_csv(self, fileName):
		self.allRecords = []
		relations = self.reportProperties['relations']
		# The following loop generates one entry to allRecords list for each record
		# that will be created. If there are any relations it acts like a
		# LEFT JOIN against the main model/table.
		for record in self.pool.get(self.model).browse(self.cr, self.uid, self.ids, self.context):
			self.allRecords += self.generate_ids( record, relations, '', [ { 'root': record } ] )

		#f = codecs.open( fileName, 'wb+', 'utf-8' )
		f = open( fileName, 'wb+' )
		csv.QUOTE_ALL = True
		# JasperReports CSV reader requires an extra colon at the end of the line.
		writer = csv.DictWriter( f, self.reportProperties['fieldNames'] + [''], delimiter=",", quotechar='"' )
		header = {}
		for field in self.reportProperties['fieldNames'] + ['']:
			if isinstance(field, unicode):
				name = field.encode('utf-8')
			else:
				name = field
			header[ field ] = name
		writer.writerow( header )
		# Once all records have been calculated, create the CSV structure itself
		for records in self.allRecords:
			row = {}
			self.generate_record_csv( records['root'], records, row, '', self.reportProperties['fields'] )
			writer.writerow( row )
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

				if isinstance(value, orm.browse_record):
					relations2 = [ f.partition('/')[2] for f in relations if f.partition('/')[0] == root and f.partition('/')[2] ]
					return self.generate_ids( value, relations2, currentPath, currentRecords )

				if not isinstance(value, orm.browse_record_list):
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

	def languages(self):
		if self._languages:
			return self._languages
		ids =self.pool.get('res.lang').search(self.cr, self.uid, [('translatable','=','1')])
		self._languages = self.pool.get('res.lang').read(self.cr, self.uid, ids, ['code'] )
		self._languages = [x['code'] for x in self._languages]
		return self._languages

	def valueInAllLanguages(self, model, id, field):
		context = copy.copy(self.context)
		values = {}
		for language in self.languages():
			if language == 'en_US':
				context['lang'] = False
			else:
				context['lang'] = language
			value = model.read(self.cr, self.uid, [id], [field], context=context)
			values[ language ] = value[0][field]

		result = []
		for key, value in values.iteritems():
			result.append( '%s~%s' % (key, value) )
		return '|'.join( result )

	def generate_record_csv(self, record, records, row, path, fields):
		# One field (many2one, many2many or one2many) can appear several times.
		# Process each "root" field only once by using a set.
		unrepeated = set( [field.partition('/')[0] for field in fields] )
		for field in unrepeated:
			root = field.partition('/')[0]
			if path:
				currentPath = '%s/%s' % (path,root)
			else:
				currentPath = root
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
			if isinstance(value, orm.browse_record):
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generate_record_csv(value, records, row, currentPath, fields2)
				continue

			# Check if it's a one2many or many2many
			if isinstance(value, orm.browse_record_list):
				if not value:
					continue
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if currentPath in records:
					self.generate_record_csv(records[currentPath], records, row, currentPath, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generate_record_csv(value[0], records, row, currentPath, fields2)
				continue

			# The field might not appear in the self.reportProperties['fields']
			# only when the field is a many2one but in this case it's null. This
			# will make the path to look like: "journal_id", when the field actually
			# in the report is "journal_id/name", for example.
			#
			# In order not to change the way we detect many2one fields, we simply check
			# that the field is in self.reportProperties['fields'] and that's it.
			if not currentPath in self.reportProperties['fields']:
				continue

			# Show all translations for a field
			type = self.reportProperties['fields'][currentPath]['type']
			if type == 'java.lang.Object':
				value = self.valueInAllLanguages(record._table, record.id, root)

			# The rest of field types must be converted into str
			if field == 'id':
				# Check for field 'id' because we can't find it's type in _columns
				value = str(value)
			elif value in (False,None):
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
			elif isinstance(value, unicode):
				value = value.encode('utf-8')
			elif not isinstance(value, str):
				value = str(value)
			row[ self.reportProperties['fields'][currentPath]['name'] ] = value

	def generate_record_xml(self, record, records, recordNode, path, fields):
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
			if isinstance(value, orm.browse_record):
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				self.generate_record_xml(value, records, fieldNode, currentPath, fields2)
				continue

			# Check if it's a one2many or many2many
			if isinstance(value, orm.browse_record_list):
				if not value:
					continue
				fields2 = [ f.partition('/')[2] for f in fields if f.partition('/')[0] == root ]
				if currentPath in records:
					self.generate_record_xml(records[currentPath], records, fieldNode, currentPath, fields2)
				else:
					# If the field is not marked to be iterated use the first record only
					self.generate_record_xml(value[0], records, fieldNode, currentPath, fields2)
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
			elif isinstance(value, str):
				value = unicode(value, 'utf-8')
			elif not isinstance(value, unicode):
				value = unicode(value)

			valueNode = self.document.createTextNode( value )
			fieldNode.appendChild( valueNode )


class report_jasper(report.interface.report_int):
	def __init__(self, name, model, parser=None ):
		# Remove report name from list of services if it already
		# exists to avoid report_int's assert. We want to keep the 
		# automatic registration at login, but at the same time we 
		# need modules to be able to use a parser for certain reports.
		if name in netsvc.SERVICES:
			del netsvc.SERVICES[name]
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
			# data_source can be 'model' or 'records' and lets parser to return
			# an empty 'records' parameter while still executing using 'records'
			data['data_source'] = d.get( 'data_source', 'model' )
			data['parameters'] = d.get( 'parameters', {} )
		r = Report( name, cr, uid, ids, data, context )
		return ( r.execute(), 'pdf' )

# Inherit ir.actions.report.xml and add an action to be able to store .jrxml and .properties
# files attached to the report so they can be used as reports in the application.
class report_xml(osv.osv):
	_name = 'ir.actions.report.xml'
	_inherit = 'ir.actions.report.xml'

	def update(self, cr, uid, ids, context={}):
		for report in self.browse(cr, uid, ids):
			attachmentIds = self.pool.get('ir.attachment').search( cr, uid, [('res_model','=','ir.actions.report.xml'),('res_id','=',report.id)], context=context)	
			has_jrxml = False
			# Browse attachments and store .jrxml and .properties into jasper_reports/custom_reports
			# directory. Also add or update ir.values data so they're shown on model views.
			for attachment in self.pool.get('ir.attachment').browse( cr, uid, attachmentIds ):
				content = attachment.datas
				fileName = attachment.datas_fname
				if not fileName or not content:
					continue
				if '.jrxml' in fileName:
					if has_jrxml:
						raise osv.except_osv(_('Error'), _('There are two .jrxml files attached to this report.'))
					has_jrxml = True
					path = self.save_file( fileName, content )
					# Update path into report_rml field.
					self.write(cr, uid, [report.id], {
						'report_rml': path
					})
					valuesId = self.pool.get('ir.values').search(cr, uid, [('value','=','ir.actions.report.xml,%s'% report.id)])
					data = {
							'name': report.name,
							'model': report.model,
							'key': 'action',
							'object': True,
							'key2': 'client_print_multi',
							'value': 'ir.actions.report.xml,%s'% report.id
					}
					if not valuesId:
						valuesId = self.pool.get('ir.values').create(cr, uid, data, context=context)
					else:
						self.pool.get('ir.values').write(cr, uid, valuesId, data, context=context)
						valuesId = valuesId[0]
				elif '.properties' in fileName:
					self.save_file( fileName, content )

				# Ensure the report is registered so it can be immediately used
				register_jasper_report( report.report_name, report.model )
		return True

	def save_file(self, name, value):
		path = os.path.abspath( os.path.dirname(__file__) )
		path += '/custom_reports/%s' % name
		f = open( path, 'wb+' )
		f.write( base64.decodestring( value ) )
		f.close()

		path = 'jasper_reports/custom_reports/%s' % name
		return path

report_xml()

# Ugly hack to avoid developers the need to register reports

import pooler
import report

def register_jasper_report(name, model):
	name = 'report.%s' % name
	# Register only if it didn't exist another "jasper_report" with the same name
	# given that developers might prefer/need to register the reports themselves.
	# For example, if they need their own parser.
	if netsvc.service_exist( name ):
		service = netsvc.SERVICES[name].parser
		if isinstance( netsvc.SERVICES[name], report_jasper ):
			return
		del netsvc.SERVICES[name]
	report_jasper( name, model )


# This hack allows automatic registration of jrxml files without 
# the need for developers to register them programatically.

old_register_all = report.interface.register_all
def new_register_all(db):
	value = old_register_all(db)

	cr = db.cursor()
	cr.execute("SELECT * FROM ir_act_report_xml WHERE auto=true ORDER BY id")
	records = cr.dictfetchall()
	cr.close()
	for record in records:
		path = record['report_rml']
		if path and path.endswith('.jrxml'):
			register_jasper_report( record['report_name'], record['model'] )
	return value

report.interface.register_all = new_register_all

