from osv import osv, fields
import base64
import xml.dom.minidom
import tempfile
import os
import shutil
import codecs
import re

import ocr
import nanscan 
from PyQt4.QtCore import *

# This class overrides the default ir_attachment class and adds the ability to
# obtain text from the file. Text is extracted using strigi and if it fails
# it will try to treat the file as an image and OCR it.
# Information found is stored in a new field called 'metainfo' that if indexed
# using the Full Text Search module it can be used to find documents easily.
class ir_attachment(osv.osv):
	_name = 'ir.attachment'
	_inherit = 'ir.attachment'
	_columns = {
		'metainfo': fields.text('Meta Information')
	}

	# This is standard create but extracting meta information first
	def create(self, cr, uid, vals, context={}):
		if 'datas' in vals:
			m = self.extractMetaInfo( vals['datas'] )
			if m != None:
				vals['metainfo'] = m
		return super(ir_attachment, self).create(cr, uid, vals, context)

	# This is standard write but extracting meta information first
	def write(self, cr, uid, ids, vals, context={}):
		if 'datas' in vals:
			m = self.extractMetaInfo( vals['datas'] )
			if m == None:
				vals['metainfo'] = ''
			else:
				vals['metainfo'] = m
		return super(ir_attachment, self).write(cr, uid, ids, vals, context)

	# Extracts data from text nodes of an XML node list
	def getText(self, nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data + " "
		return rc

	# Extracts meta information from the given parameter which should be in base64
	def extractMetaInfo(self, data):
		# First of all we'll see what strigi can do for us. If there is a text tag
		# it means it's some kind of text file (plain text, pdf, ps, doc, odf, etc..)
		# Otherwise, we'll try to treat it as an image, and OCR it.
		if not data:
			return ''
		dir=tempfile.mkdtemp()
		buf = base64.decodestring(data)
		f = open('%s/object.tmp' % dir,'wb')
		f.write( buf )
		f.close()

		# Analyze strigi's xmlindexer output
		output = os.popen('xmlindexer %s' % dir).read()
		dom = xml.dom.minidom.parseString( output )
		tags = dom.getElementsByTagName( 'text' )
		if len(tags):
			metaInfo = self.getText(tags[0].childNodes).strip()
		else:
			# We couldn't get text information with strigi, let's try if it's an image
			os.spawnlp(os.P_WAIT, 'convert', 'convert', dir + '/object.tmp', dir + '/object.tif' )
			if os.path.exists( dir + '/object.tif' ):
				c = ocr.Classifier()
				c.prepareImage( dir + '/object.tif' )
				r = c.ocr()
				metaInfo = r['text'].strip()
				# TODO: Use language detection to choose different dictionary in TSearch2?
				# If so, that should apply to text/pdf/etc.. files too
				#r['language']
			else:
				metaInfo = None
		shutil.rmtree( dir, True )
		return metaInfo
ir_attachment()


class nan_template(osv.osv):
	_name = 'nan.template'
	_columns = {
		'name' : fields.char('Name', 64, required=True),
		'boxes' : fields.one2many('nan.template.box', 'template_id', 'Boxes'),
		'attach_function' : fields.char('Attachment Function', 256),
		'action_function' : fields.char('Action Function', 256),
		'documents' : fields.one2many('nan.document', 'template_id', 'Documents')
	}

	# Returns a Template from the fields of a template. You'll usually use 
	# getTemplateFromId() or getAllTemplates()
	def getTemplateFromData(self, cr, uid, data):
		template = nanscan.Template( data['name'] )
		template.id = data['id']
		ids = self.pool.get('nan.template.box').search( cr, uid, [('template_id','=',data['id'])] )
		boxes = self.pool.get('nan.template.box').read(cr, uid, ids)
		for y in boxes:
			box = nanscan.TemplateBox()
			box.rect = QRectF( y['x'], y['y'], y['width'], y['height'] )
			box.name = y['name']
			box.text = y['text']
			box.recognizer = y['recognizer']
			box.type = y['type']
			box.filter = y['filter']
			# Important step: ensure box.text is unicode!
			if isinstance( box.text, str ):
				box.text = unicode( box.text, 'latin-1' )
			template.addBox( box )
		print "GETTING TEMPLATE: %s WITH %d BOXES" % ( data['name'], len(boxes) )
		return template

	# Returns a Template from the given id
	def getTemplateFromId(self, cr, uid, id):
		templates = self.pool.get('nan.template').read(cr, uid, [id])
		if not templates:
			return None
		return self.getTemplateFromData( cr, uid, templates[0] )

	# Returns all templates in a list of objects of class Template
	def getAllTemplates(self, cr, uid):
		# Load templates into 'templates' list
		templates = []
		ids = self.pool.get('nan.template').search(cr, uid, [])
		templateValues = self.pool.get('nan.template').read(cr, uid, ids)
		for x in templateValues:
			templates.append( self.getTemplateFromData( cr, uid, x ) )
		return templates


nan_template()

class nan_template_box(osv.osv):
	_name = 'nan.template.box'
	_columns = {
		'template_id' : fields.many2one('nan.template', 'Template', required=True, ondelete='cascade'),
		'x' : fields.float('X'),
		'y' : fields.float('Y'),
		'width' : fields.float('Width'),
		'height' : fields.float('Height'),
		'name' : fields.char('Name', 256),
		'text' : fields.char('Text', 256),
		'recognizer': fields.selection( [('text','Text'),('barcode','Barcode')], 'Recognizer' ),
		'type' : fields.selection( [('matcher','Matcher'),('input','Input')], 'Type' ),
		'filter' : fields.selection( [('numeric','Numeric'), ('alphabetic','Alphabetic'), ('alphanumeric','Alphanumeric'), ('exists', 'Exists'), ('none', 'None')], 'Filter' )
	}
nan_template_box()

def attachableDocuments(self, cr, uid, context={}):
        obj = self.pool.get('ir.model')
	ids = obj.search(cr, uid, [])
	res = obj.read(cr, uid, ids, ['model', 'name'], context)
	return [(r['model'], r['name']) for r in res]

class nan_document(osv.osv):
	_name = 'nan.document'
	_columns = {
		'name' : fields.char('Name', 64),
		'datas': fields.binary('Data'),
		'properties': fields.one2many('nan.document.property', 'document_id', 'Properties'),
		'template_id': fields.many2one('nan.template', 'Template' ),
		'document': fields.reference('Document', selection=attachableDocuments, size=128),
		'task' : fields.text('Task', readonly=True),
		'state': fields.selection( [('pending','Pending'),('scanned','Scanned'),
			('verified','Verified'),('processed','Processed')], 
			'State', required=True, readonly=True )
	}
	_defaults = {
		'state': lambda *a: 'pending'
	}

	def write(self, cr, uid, ids, values, context=None):
		# Scan after writting as it will modify the objects and thus a "modified in 
		# the meanwhile" would be thrown, so by now check which of the records
		# we'll want to scan later
		toScan = []
		if 'template_id' in values:
			for x in self.read( cr, uid, ids, ['state', 'template_id'], context ):
				# We only scan the document if template_id has changed and the document
				# is in 'scanned' state.
				if x['state'] == 'scanned' and x['template_id'] != values['template_id']:
					toScan.append( {'id': x['id'], 'template_id': values['template_id'] } )

		ret = super(nan_document, self).write(cr, uid, ids, values, context)

		for x in toScan:
			self.scanDocumentWithTemplate( cr, uid, x['id'], x['template_id'] )
		return ret

	def scan_document(self, cr, uid, imageIds):
		# Load templates into 'templates' list
		templates = self.pool.get('nan.template').getAllTemplates( cr, uid )

		# Initialize Ocr System (Gamera)
		nanscan.initOcrSystem()
		recognizer = nanscan.Recognizer()

		# Iterate over all images and try to find the most similar template
		for document in self.browse(cr, uid, imageIds):
			#TODO: Enable workflow test 
			#if document.state != 'pending':
			#	continue
			image = '/tmp/image.png'
			fp = file(image,'wb+')
			fp.write( base64.decodestring(document.datas) )
			fp.close()
			result = recognizer.findBestTemplate( cr, image, templates)
			template = result['template']
			doc = result['document']
			if not template:
				print "No template found for document %s." % document.name
			else:
				print "The best template found for document %s is %s." % (document.name, template.name)

			if template:
				template_id = template.id
			else:
				template_id = False
			self.write(cr, uid, [document.id], {'template_id': template_id, 'state': 'scanned'})
			if doc:
				obj = self.pool.get('nan.document.property')
				for box in doc.boxes:
					obj.create(cr, uid, { 'name' : box.templateBox.name, 'value' : box.text, 'document_id': document.id } )

		self.executeAttachs( cr, uid, imageIds )
		self.executeActions( cr, uid, imageIds, True )
		cr.commit()

	def scanDocumentWithTemplate(self, cr, uid, documentId, templateId):

		# Whether templateId is valid or not
		# Remove previous properties
		obj = self.pool.get('nan.document.property')
		ids = obj.search( cr, uid, [('document_id','=',documentId)] )
		obj.unlink( cr, uid, ids )

		if templateId:
			# Initialize Ocr System (Gamera)
			nanscan.initOcrSystem()
			recognizer = nanscan.Recognizer()

			template = self.pool.get('nan.template').getTemplateFromId( cr, uid, templateId )  

			documents = self.read(cr, uid, [documentId])
			if not documents:
				return 
			document = documents[0]

			image = '/tmp/image.png'
			fp = file( image, 'wb+')
			fp.write( base64.decodestring( document['datas'] ) )
			fp.close()
			doc = recognizer.scanWithTemplate( image, template )

			for box in doc.boxes:
				obj.create(cr, uid, { 'name' : box.templateBox.name, 'value' : box.text, 'document_id': document['id'] } )
		self.executeAttachs( cr, uid, [documentId] )
		self.executeActions( cr, uid, [documentId], True )
		cr.commit()

	def process_document(self, cr, uid, ids):
		self.executeActions( cr, uid, ids, False )
		cr.commit()

	def _parseFunction(self, function, properties):
		expression = re.match('(.*)\((.*)\)', function)
		name = expression.group(1)
		parameters = expression.group(2)
		if name not in dir(self):
			print "Function '%s' not found" % (name)
			return False

		parameters = parameters.split(',')
		newParameters = []
		for p in parameters:
			value = p.strip()
			if value.startswith( '#' ):
				if value[1:] not in properties:
					print "Property '%s' not found" % value
					newParameters.append( "''" )
					continue
				value = properties[ value[1:] ]
			value = "'" + value.replace("'","\\'") + "'"
			if type(value) != unicode:
				value = unicode( value, errors='ignore' )
			newParameters.append( value )
		return (name, newParameters)

	def executeActions( self, cr, uid, ids, explain ):
		for document in self.browse( cr, uid, ids ):
			#TODO: Enable workflow test 
			#if not explain and document.state != 'verified':
				#continue

			task = None
			if document.template_id:
				function = document.template_id.action_function
				if function:
					properties = dict( [(x.name, unicode(x.value)) for x in document.properties] )
					(name, parameters) = self._parseFunction(function, properties)

					obj = self.pool.get('nan.document')
					task = eval('obj.%s(cr, uid, explain, %s)' % ( name, ','.join( parameters ) ) )
			if explain:
				self.write( cr, uid, [document.id], {'task': task} )
			elif document.document:
				# Attach document to the appropiate reference
				ref = document.document.split(',')
				model = ref[0]
				id = ref[1]
				attach = { 
					'res_id': id,
					'res_model': model,
					'name': document.name,
					'datas': document.datas,
					'datas_fname': document.name,
					'description': 'Attached automatically'
				}
				self.pool.get( 'ir.attachment' ).create( cr, uid, attach )
				self.write(cr, uid, [document.id], {'state': 'processed'})


	def executeAttachs( self, cr, uid, ids ):
		for document in self.browse( cr, uid, ids ):
			reference = None
			if document.template_id:
				function = document.template_id.attach_function
				if function:
					properties = dict( [(x.name, unicode( x.value, 'latin-1' )) for x in document.properties] )

					(name, parameters) = self._parseFunction(function, properties)
					obj = self.pool.get('nan.document')
					#print 'CALLING: obj.%s(cr, uid, %s)' % ( name, u','.join( parameters ) ), 
					reference = eval('obj.%s(cr, uid, %s)' % ( name, u','.join( parameters ) ) )

			if reference:
				self.write( cr, uid, [document.id], {'document': '%s,%s' % (reference[0],reference[1]) } )
			else:
				self.write( cr, uid, [document.id], {'document': False} )

			#expression = re.match('(.*)\((.*)\)', function)
			#name = expression.group(1)
			#parameters = expression.group(2)
			#if name not in dir(self):
			#	print "Function '%s' not found" % (name)
			#	continue
			#parameters = parameters.split(',')
			#properties = dict( [(x.name, x.value) for x in document.properties] )
			#newParameters = []
			#for p in parameters:
			#	value = p.strip()
			#	if value.startswith( '#' ):
			#		print "We'll search '%s' in the properties" % value[1:]
			#		if value[1:] not in properties:
			#			continue
			#		value = properties[ value[1:] ]
			#	value = "'" + value.replace("'","\\\\'") + "'"
			#	newParameters.append( value )

			#obj = self.pool.get('nan.document')
			#reference = eval('obj.%s(cr, uid, %s)' % ( name, ','.join( newParameters ) ) )



	def actionAddPartner( self, cr, uid, explain, name ):
		if explain:
			return "A new partner with name '%s' will be created (if it doesn't exist already)." % name
		else:
			if not self.pool.get( 'res.partner' ).search( cr, uid, [('name','=',name)]):
				self.pool.get( 'res.partner' ).create( cr, uid, {'name': name} )
			return True

	def attachModelByField( self, cr, uid, model, field, name ):
		table = self.pool.get( model )._table
		# TODO: Security issues
		cr.execute( 'SELECT id FROM "' + table + '" ORDER BY similarity("' + field + '",\'%s\') DESC LIMIT 1' % name ) 
		record = cr.fetchone()
		if not record:
			return False
		return ( model, record[0] )

		
nan_document()

class nan_document_property(osv.osv):
	_name = 'nan.document.property'
	_columns = {
		'name' : fields.char('Text', 256),
		'value' : fields.char('Value', 256),
		'document_id' : fields.many2one('nan.document', 'Document', required=True, ondelete='cascade')
	}
nan_document_property()	
