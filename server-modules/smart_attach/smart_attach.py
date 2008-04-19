from osv import osv, fields
import base64
import xml.dom.minidom
import tempfile
import os
import shutil
import codecs
import re

import ocr
import scan
from template import *

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


# Smarter processing models and functions

def translate(text):
	txt = text
	f=codecs.open('addons/smart_attach/translations.txt', 'r', 'utf-8')
	if not f:
		print "File not found"
		return txt
	translations = f.readlines()
	f.close()
	for x in translations:
		for y in x[1:]:
			txt = txt.replace( y, x[0] )
	return txt

def findBestTemplate( cr, image, templates ):
	os.spawnlp(os.P_WAIT, 'convert', 'convert', image, '/tmp/image.tif' )
	if not os.path.exists( '/tmp/image.tif' ):
		return None
	c = scan.Ocr()
	c.scan( '/tmp/image.tif' )
	max = 0
	bestDocument = Document()
	bestTemplate = None
	for template in templates:
		currentDocument = Document()

		if not template.boxes:
			continue
		score = 0
		matcherBoxes = 0
		for templateBox in template.boxes:
			if not templateBox.text:
				continue
			text = c.textInRegion( templateBox.rect )
			documentBox = DocumentBox()
			documentBox.text = text
			documentBox.templateBox = templateBox
			currentDocument.addBox( documentBox )

			if templateBox.type != 'matcher':
				print "Jumping %s due to type %s " % ( templateBox.name, templateBox.type )
				continue
			matcherBoxes += 1
			#cr.execute( 'SELECT similarity(%s,%s)', (translate(text), translate(templateBox.text)) )
			cr.execute( 'SELECT similarity(%s,%s)', (text, templateBox.text) )
			similarity = cr.fetchone()[0]
			score += similarity
		score = score / matcherBoxes
		if score > max:
			max = score
			bestTemplate = template
			bestDocument = currentDocument
		print "Template %s has score %s" % (template.name, score)
	return { 'template': bestTemplate, 'document': bestDocument }

class nan_template(osv.osv):
	_name = 'nan.template'
	_columns = {
		'name' : fields.char('Name', 64, required=True),
		'boxes' : fields.one2many('nan.template.box', 'template_id', 'Boxes'),
		'attach_function' : fields.char('Attachment Function', 256),
		'action_function' : fields.char('Action Function', 256),
		'documents' : fields.one2many('nan.document.queue', 'template_id', 'Documents')
	}

nan_template()

class nan_template_box(osv.osv):
	_name = 'nan.template.box'
	_columns = {
		'template_id' : fields.many2one('nan.template', 'Template', required=True, ondelete='cascade'),
		'x' : fields.integer('X'),
		'y' : fields.integer('Y'),
		'width' : fields.integer('Width'),
		'height' : fields.integer('Height'),
		'name' : fields.char('Name', 256),
		'text' : fields.char('Text', 256),
		'type' : fields.selection( [('matcher','Matcher'),('input','Input')], 'Type' ),
		'filter' : fields.selection( [('numeric','Numeric'), ('alphabetic','Alphabetic'), ('alphanumeric','Alphanumeric'), ('none', 'None')], 'Filter' )
	}
nan_template_box()

def attachableDocuments(self, cr, uid, context={}):
        obj = self.pool.get('ir.model')
	ids = obj.search(cr, uid, [])
	res = obj.read(cr, uid, ids, ['model', 'name'], context)
	return [(r['model'], r['name']) for r in res]

class nan_document_queue(osv.osv):
	_name = 'nan.document.queue'
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

	def scan_document(self, cr, uid, imageIds):
		# Load templates into 'templates' list
		templates = []
		ids = self.pool.get('nan.template').search(cr, uid, [])
		templateValues = self.pool.get('nan.template').read(cr, uid, ids)
		for x in templateValues:
			template = Template( x['name'] )
			template.id = x['id']
			ids = self.pool.get('nan.template.box').search( cr, uid, [('template_id','=',x['id'])] )
			boxes = self.pool.get('nan.template.box').read(cr, uid, ids)
			for y in boxes:
				box = TemplateBox()
				box.rect = QRectF( y['x'], y['y'], y['width'], y['height'] )
				box.name = y['name']
				box.text = y['text']
				box.type = y['type']
				box.filter = y['filter']
				# Important step: ensure box.text is unicode!
				if isinstance( box.text, str ):
					box.text = unicode( box.text, 'latin-1' )
				template.addBox( box )
			templates.append(template)

		# Initialize Ocr System (Gamera)
		scan.initOcrSystem()

		# Iterate over all images and try to find the most similar template
		for document in self.browse(cr, uid, imageIds):
			#TODO: Enable workflow test 
			#if document.state != 'pending':
			#	continue
			fp = file('/tmp/image.png','wb+')
			fp.write( base64.decodestring(document.datas) )
			fp.close()
			result = findBestTemplate( cr, '/tmp/image.png', templates)
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
		#print "P: ", properties
		newParameters = []
		for p in parameters:
			value = p.strip()
			if value.startswith( '#' ):
				print "We'll search '%s' in the properties" % value[1:]
				if value[1:] not in properties:
					continue
				value = properties[ value[1:] ]
			value = "'" + value.replace("'","\\\\'") + "'"
			newParameters.append( value )
		return (name, newParameters)

	def executeActions( self, cr, uid, ids, explain ):
		for document in self.browse( cr, uid, ids ):
			#TODO: Enable workflow test 
			#if not explain and document.state != 'verified':
				#continue

			if not document.template_id:
				print "Document '%s' has no template associated" % document.name
				continue
			function = document.template_id.action_function
			if not function:
				print "Template '%s' has no attach function" % document.template_id.name
				continue

			properties = dict( [(x.name, x.value) for x in document.properties] )
			(name, parameters) = self._parseFunction(function, properties)

			obj = self.pool.get('nan.document.queue')
			result = eval('obj.%s(cr, uid, explain, %s)' % ( name, ','.join( parameters ) ) )
			if explain:
				self.write( cr, uid, [document.id], {'task': result} )
			elif document.document:
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
			if not document.template_id:
				print "Document '%s' has no template associated" % document.name
				continue
			function = document.template_id.attach_function
			if not function:
				print "Template '%s' has no attach function" % document.template_id.name
				continue
			expression = re.match('(.*)\((.*)\)', function)
			name = expression.group(1)
			parameters = expression.group(2)
			if name not in dir(self):
				print "Function '%s' not found" % (name)
				continue
			parameters = parameters.split(',')
			properties = dict( [(x.name, x.value) for x in document.properties] )
			newParameters = []
			for p in parameters:
				value = p.strip()
				if value.startswith( '#' ):
					print "We'll search '%s' in the properties" % value[1:]
					if value[1:] not in properties:
						continue
					value = properties[ value[1:] ]
				value = "'" + value.replace("'","\\\\'") + "'"
				newParameters.append( value )

			obj = self.pool.get('nan.document.queue')
			reference = eval('obj.%s(cr, uid, %s)' % ( name, ','.join( newParameters ) ) )
			self.write( cr, uid, [document.id], {'document': '%s,%s' % (reference[0],reference[1]) } )


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

		
nan_document_queue()

class nan_document_property(osv.osv):
	_name = 'nan.document.property'
	_columns = {
		'name' : fields.char('Text', 256),
		'value' : fields.char('Value', 256),
		'document_id' : fields.many2one('nan.document.queue', 'Document', required=True, ondelete='cascade')
	}
nan_document_property()	
