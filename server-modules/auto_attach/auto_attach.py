##############################################################################
#
# Copyright (c) 2007-2010 NaN Projectes de Programari Lliure, S.L. All rights reserved
#                         http://www.NaN-tic.com
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
# as published by the Free Software Foundation; either version 3
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

import re
import os
import codecs
import base64
import shutil
import tempfile
import xml.dom.minidom

from osv import osv
from osv import fields
from tools.translate import _

from NanScan.Template import *
from NanScan.Document import *
from NanScan.Recognizer import *
from NanScan.Ocr import *

from PyQt4.QtCore import *


class nan_template(osv.osv):
	_name = 'nan.template'
	_columns = {
		'name' : fields.char('Name', 64, required=True),
		'box_ids' : fields.one2many('nan.template.box', 'template_id', 'Boxes'),
		'attach_function' : fields.char('Attachment Function', 256),
		'action_function' : fields.char('Action Function', 256),
		'document_ids' : fields.one2many('nan.document', 'template_id', 'Documents')
	}

	# Returns a Template from the fields of a template. You'll usually use 
	# getTemplateFromId() or getAllTemplates()
	def getTemplateFromData(self, cr, uid, data, context=None):
		template = Template( data['name'] )
		template.id = data['id']
		ids = self.pool.get('nan.template.box').search( cr, uid, [('template_id','=',data['id'])], context=context )
		boxes = self.pool.get('nan.template.box').read(cr, uid, ids, context=context)
		for y in boxes:
			box = TemplateBox()
			box.id = y['id']
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
		return template

	# Returns a Template from the given id
	def getTemplateFromId(self, cr, uid, id, context=None):
		templates = self.pool.get('nan.template').read(cr, uid, [id], context=context)
		if not templates:
			return None
		return self.getTemplateFromData( cr, uid, templates[0], context )

	# Returns all templates in a list of objects of class Template
	def getAllTemplates(self, cr, uid, context=None):
		# Load templates into 'templates' list
		templates = []
		ids = self.pool.get('nan.template').search(cr, uid, [], context=context)
		templateValues = self.pool.get('nan.template').read(cr, uid, ids, context=context)
		for x in templateValues:
			templates.append( self.getTemplateFromData( cr, uid, x, context ) )
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
		'feature_x' : fields.float('Feature X'),
		'feature_y' : fields.float('Feature Y'),
		'feature_width' : fields.float('Feature Width'),
		'feature_height' : fields.float('Feature Height'),
		'name' : fields.char('Name', 256),
		'text' : fields.char('Text', 256),
		'recognizer': fields.selection( [('text','Text'),('barcode','Barcode'),('dataMatrix','Data Matrix')], 'Recognizer' ),
		'type' : fields.selection( [('matcher','Matcher'),('input','Input')], 'Type' ),
		'filter' : fields.selection( [('numeric','Numeric'), ('alphabetic','Alphabetic'), ('alphanumeric','Alphanumeric'), ('exists', 'Exists'), ('none', 'None')], 'Filter' )
	}
nan_template_box()

def attachableDocuments(self, cr, uid, context={}):
	ids = self.pool.get('ir.model').search(cr, uid, [], context=context)
	res = self.pool.get('ir.model').read(cr, uid, ids, ['model', 'name'], context)
	return [(r['model'], r['name']) for r in res]

class nan_document(osv.osv):
	_name = 'nan.document'
	state_only_read = {
		'pending': [ ( 'readonly', False ), ],
		'scanned': [ ( 'readonly', False ), ],
	}
	_columns = {
		'name' : fields.char('Name', 64, readonly=True, states=state_only_read),
		'datas': fields.binary('Data', readonly=True, states=state_only_read),
		'property_ids': fields.one2many('nan.document.property', 'document_id', 'Properties', readonly=True, states=state_only_read),
		'template_id': fields.many2one('nan.template', 'Template', readonly=True, states=state_only_read),
		'document_id': fields.reference('Document', selection=attachableDocuments, size=128, readonly=True, states=state_only_read),
		'task' : fields.text('Task', readonly=True),
		'state': fields.selection( [
			('pending','Pending'),('scanning','Scanning'),('scanned','Scanned'),
			('verified','Verified'),('processing','Processing'),('processed','Processed')], 
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
				# We only scan the document if template has changed and the document
				# is in 'scanned' state.
				if x['state'] == 'scanned' and x['template_id'] != values['template_id']:
					toScan.append( {'id': x['id'], 'template_id': values['template_id'] } )

		ret = super(nan_document, self).write(cr, uid, ids, values, context)

		for x in toScan:
			self.scanDocumentWithTemplate( cr, uid, x['id'], x['template_id'] )
		return ret

	def scan_document_background(self, cr, uid, imageIds, context=None):
		self.pool.get('ir.cron').create(cr, uid, {
			'name': 'Scan document',
			'user_id': uid,
			'model': 'nan.document',
			'function': 'scan_document',
			'args': repr([ imageIds, True ])
		}, context)
		cr.commit()

	def scan_documents_batch(self, cr, uid, imageIds, context=None):
		self.scan_document(cr, uid, imageIds, context=context)
		self.pool.get('res.request').create( cr, uid, {
			'act_from': uid,
			'act_to': uid,
			'name': 'Finished scanning documents',
			'body': 'The auto_attach system has finished scanning the documents you requested. You can now go to the Scanned Documents queue to verify and process them.',
		}, context)

	# If notify=True sends a request/notification to uid
	def scan_document(self, cr, uid, imageIds, notify=False, context=None):
		# Load templates into 'templates' list
		templates = self.pool.get('nan.template').getAllTemplates( cr, uid, context )

		# Initialize Ocr System (Gamera)
		recognizer = Recognizer()

		# Iterate over all images and try to find the most similar template
		for document in self.browse(cr, uid, imageIds, context):
			if document.state not in ('pending','scanning'):
				continue
			if not document.datas:
				continue
			fp, image = tempfile.mkstemp()
			fp = os.fdopen( fp, 'wb+' )
			fp.write( base64.decodestring(document.datas) )
			fp.close()
			recognizer.recognize( QImage( image ) )
			
			result = recognizer.findMatchingTemplateByOffset( templates )
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
			self.write(cr, uid, [document.id], {
				'template_id': template_id, 
				'state': 'scanned'
			}, context=context)
			if doc:
				for box in doc.boxes:
					self.pool.get('nan.document.property').create(cr, uid, { 
						'name': box.templateBox.name, 
						'value': box.text, 
						'document_id': document.id,
						'template_box_id': box.templateBox.id
					}, context)

			if notify:
				self.pool.get('res.request').create( cr, uid, {
					'act_from': uid,
					'act_to': uid,
					'name': 'Finished scanning document',
					'body': 'The auto_attach system has finished scanning the document you requested. A reference to the document can be found in field Document Ref 1.',
					'ref_doc1': 'nan.document,%d' % document.id,
				}, context)

		self.executeAttachs( cr, uid, imageIds, context )
		self.executeActions( cr, uid, imageIds, True, context )

		cr.commit()

	def scanDocumentWithTemplate(self, cr, uid, documentId, templateId, context):

		# Whether templateId is valid or not
		# Remove previous properties
		ids = self.pool.get('nan.document.property').search( cr, uid, [('document_id','=',documentId)], context=context )
		self.pool.get('nan.document.property').unlink( cr, uid, ids, context )

		if templateId:
			template = self.pool.get('nan.template').getTemplateFromId( cr, uid, templateId, context )  

			documents = self.read(cr, uid, [documentId], context=context)
			if not documents:
				return 
			document = documents[0]

			fp, image = tempfile.mkstemp()
			fp = os.fdopen( fp, 'wb+' )
			fp.write( base64.decodestring( document['datas'] ) )
			fp.close()

			recognizer = Recognizer()
			recognizer.recognize( QImage( image ) )
			doc = recognizer.extractWithTemplate( image, template )

			for box in doc.boxes:
				obj.create(cr, uid, {
					'name': box.templateBox.name, 
					'value': box.text, 
					'document_id': document['id'],
					'template_box_id': box.templateBox.id
				}, context)
		self.executeAttachs( cr, uid, [documentId], context )
		self.executeActions( cr, uid, [documentId], True, context )
		cr.commit()

	def process_document(self, cr, uid, ids, context=None):
		self.executeActions( cr, uid, ids, False, context )
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

	def executeActions( self, cr, uid, ids, explain, context ):
		for document in self.browse( cr, uid, ids, context ):
			print "Executing action on document with state ", document.state, explain
			if not explain and document.state not in ('verified','processing'):
				continue

			task = None
			if document.template_id:
				function = document.template_id.action_function
				if function:
					properties = dict( [(x.name, unicode(x.value)) for x in document.property_ids] )
					(name, parameters) = self._parseFunction(function, properties)

					obj = self.pool.get('nan.document')
					task = eval('obj.%s(cr, uid, explain, %s)' % ( name, ','.join( parameters ) ) )
			if explain:
				self.write( cr, uid, [document.id], {'task': task} )
			elif document.document_id:
				# Attach document to the appropiate reference
				ref = document.document_id.split(',')
				model = ref[0]
				id = ref[1]
				self.pool.get( 'ir.attachment' ).create( cr, uid, { 
					'res_id': id,
					'res_model': model,
					'name': document.name,
					'datas': document.datas,
					'datas_fname': document.name,
					'description': 'Document attached automatically'
				}, context)
				self.write(cr, uid, [document.id], {
					'state': 'processed'
				}, context)


	def executeAttachs( self, cr, uid, ids, context=None ):
		for document in self.browse( cr, uid, ids, context ):
			reference = None
			if document.template_id:
				function = document.template_id.attach_function
				if function:
					properties = dict( [(x.name, x.value) for x in document.property_ids] )

					(name, parameters) = self._parseFunction(function, properties)
					obj = self.pool.get('nan.document')
					#print 'CALLING: obj.%s(cr, uid, %s)' % ( name, u','.join( parameters ) ), 
					reference = eval('obj.%s(cr, uid, %s)' % ( name, u','.join( parameters ) ) )

			if reference:
				self.write( cr, uid, [document.id], {
					'document_id': '%s,%s' % (reference[0],reference[1]) 
				}, context )
			else:
				self.write( cr, uid, [document.id], {
					'document_id': False
				}, context )


	def actionAddPartner( self, cr, uid, explain, name ):
		if explain:
			return _("A new partner with name '%s' will be created (if it doesn't exist already).") % name

		if not self.pool.get( 'res.partner' ).search( cr, uid, [('name','=',name)]):
			self.pool.get( 'res.partner' ).create( cr, uid, {
				'name': name
			})
		return True

	def attachModelByField( self, cr, uid, model, field, name ):
		# Note: The commented code below has security issues and it is here as a example only. 
		#table = self.pool.get( model )._table
		#cr.execute( 'SELECT id FROM "' + table + '" ORDER BY similarity("' + field + '",\'%s\') DESC LIMIT 1' % name ) 
		#record = cr.fetchone()
		#if not record:
		#	return False
		#return ( model, record[0] )

		ids = self.pool.get(model).search(cr, uid, [(field,'=',name)])
		if not ids:
			return False
		return ( model, ids[0] )
		

nan_document()

class nan_document_property(osv.osv):
	_name = 'nan.document.property'
	_columns = {
		'name' : fields.char('Text', 256),
		'value' : fields.char('Value', 256),
		'document_id' : fields.many2one('nan.document', 'Document', required=True, ondelete='cascade'),
		'template_box_id' : fields.many2one('nan.template.box', 'Template Box', required=True, ondelete='set null')
	}
nan_document_property()	

