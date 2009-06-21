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

from osv import osv, fields
from service import security
import netsvc 
import sql_db
import pooler

class nan_semantic_services(netsvc.Service):
	def __init__(self, name="semantic"):
		netsvc.Service.__init__(self, name)
		self.joinGroup('web-services')
		self.exportMethod(self.setRating)
		self.exportMethod(self.rating)
		self.exportMethod(self.tags)
		self.exportMethod(self.description)
		self.exportMethod(self.contacts)

	def setRating(self, db, uid, passwd, model, ids, fields, rating, context={}):
		self.setValue(db, uid, passwd, model, ids, fields, 'rating', rating, context)
		return True

	def rating(self, db, uid, passwd, model, ids, field, context={}):
		res = self.value(db, uid, passwd, model, ids, field, 'rating', context)
		for key in res.keys():
			res[str(key)] = int(res[key])
		return res

	def tags(self, db, uid, passwd, model, ids, field, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)

		mids = pool.get('ir.model').search(cr, uid, [('model','=',model)], context=context)
		modelName = pool.get('ir.model').read(cr, uid, mids, ['name'], context=context)[0]['name']

		commonTags = [ 'OpenERP', modelName ]

		res = {}
		for id in ids:
			ts = commonTags[:]
			if model == 'ir.attachment':
				modelName = pool.get('ir.attachment').read(cr, uid, id, ['res_model'], context=context)['res_model']
				mids = pool.get('ir.model').search(cr, uid, [('model','=',modelName)], context=context)
				modelName = pool.get('ir.model').read(cr, uid, mids, ['name'], context=context)[0]['name']
				ts.append( modelName )
			res[str(id)] = ts
		return res

	def description(self, db, uid, passwd, model, ids, field, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)
		
		descriptionField = None
		columns = pool.get( model )._columns
		possibleFields = ['description', 'notes', 'note', 'comment', 'comments']
		for f in possibleFields:
			if f in columns:
				descriptionField = f
		res = {}
		data = pool.get( model ).read(cr, uid, ids, ['id', descriptionField], context=context)
		for record in data:
			if descriptionField and record[descriptionField]:
				value = record[descriptionField]
			else:
				value = ''
			res[ str(record['id']) ] = value
		return res

	def contacts(self, db, uid, passwd, model, ids, field, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)
		
		# Try to find if there's any relation with 'res.partner.address' (or 'res.partner')
		# in the given model:
		addressField = None
		partnerField = None
		columns = pool.get( model )._columns
		for key, value in columns.iteritems():
			if value._type == 'many2one':
				if value._obj == 'res.partner.address':
					addressField = key
					break
				elif value._obj == 'res.parnter':
					partnerField = key
			elif value._type == 'one2many' and value._obj == 'res.partner.address':
					addressField = key
			elif value._type == 'many2many' and value._obj == 'res.partner.address':
					addressField = key

		# Now that we have which field relates to 'res.partner.address' (or 'res.partner')
		# browse all records and return a list of e-mails for each of them.
		res = {}
		for record in pool.get( model ).browse( cr, uid, ids, context=context ):
			emails = []
			if model == 'res.partner.address':
				if r.email:	
					emails = [r.email]
			elif addressField:
				value = record.__getattr__(addressField)
				if value and isinstance(value, osv.orm.browse_record):
					if value.email:
						emails = [value.email]
				elif value and isinstance(value, osv.orm.browse_record_list):
					emails = [x.email for x in record.address if x.email]
			elif partnerField:
				value = record.__getattr__(partnerField)
				if value:
					emails = [x.email for x in value.address if x.email]
			res[ str(record.id) ] = [ email.strip() for email in emails ]
		return res

	def setValue(self, db, uid, passwd, model, ids, fields, predicate, value, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)
		model = pool.get('ir.model').search(cr, uid, [('model','=',model)])[0]
		data = {
			'subject_model': model,
			'predicate': predicate,
			'object': value
		}
		for id in ids:
			data[ 'subject_id' ] = id
			data[ 'subject_field' ] = None
			pool.get('nan.semantic.triple').create(cr, uid, data )
			for field in fields:
				data[ 'subject_field' ] = field
				pool.get('nan.semantic.triple').create(cr, uid, data )
		return True

	def value(self, db, uid, passwd, model, ids, field, predicate, context={}):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)
		modelId = pool.get('ir.model').search(cr, uid, [('model','=',model)])[0]
		query = [('subject_model','=',modelId),('subject_id','in',ids),('predicate','=',predicate)]
		if field:
			print "FIELD: ", field
			fieldId = pool.get('ir.model.fields').search(cr, uid, [('model','=',modelId),('name','=',field)])[0]
			query.append( ('subject_field','=',fieldId) )
		tripleIds = pool.get('nan.semantic.triple').search(cr, uid, query)
		data = pool.get('nan.semantic.triple').read(cr, uid, tripleIds, ['subject_id','object'])
		d = {}
		for x in data:
			d[ str(x['subject_id']) ] = x['object']
		for x in ids:
			if str(x) not in d:
				d[ str(x) ] = -1
		return d
nan_semantic_services()

class nan_semantic_triple(osv.osv):
	_name = 'nan.semantic.triple'
	_description = 'Triple'	

	def _all_models(self, cr, uid, context={}):
		ids = self.pool.get('ir.model').search(cr, uid, [], context=context)
		data = self.pool.get('ir.model').read(cr, uid, ids, ['model','name'])
		return [(x['model'], x['name']) for x in data]
	
	def _reference(self, cr, uid, ids, field_name, arg, context={}):
		print "IDS: ", ids
		res = {}
		for record in self.browse(cr, uid, ids):
			res[ record.id ] = '%s,%d' % (record.subject_model.model, record.subject_id)
		return res

	def create(self, cr, uid, vals, context=None):
		if not context:
			context = {}
		print "CONTEXT: ", context
		if 'subject_model' in context:
			ids = self.pool.get('ir.model').search(cr, uid, [('model','=',context['subject_model'])])
			if ids:
				vals['subject_model'] = ids[0]
		if 'subject_id' in context:
			vals['subject_id'] = context['subject_id']
		return super(nan_semantic_triple,self).create(cr, uid, vals, context)

	_columns = {
		'subject': fields.function(_reference, method=True, string='Subject', type='reference', selection=_all_models, size=128),
		'subject_model': fields.many2one('ir.model', 'Subject Model', required=True, size=64),
		'subject_id': fields.integer('Subject Id', required=True),
		'subject_field': fields.many2one('ir.model.fields', 'Subject Field', size=64),
		'predicate': fields.char('Predicate', required=True, size=256),
		'object': fields.char('Object', required=True, size=256),
	}

	def _default_subject(self, cr, uid, context):
		if 'subject_model' in context and 'subject_id' in context:
			return '%s,%d' % ( context['subject_model'], context['subject_id'] )
		return False

	_defaults = {
		'subject': _default_subject 
	}
nan_semantic_triple()

class nan_semantic_ontology(osv.osv):
	_name = 'nan.semantic.ontology'
	_description = 'Ontology'

	_columns = {
		'field': fields.many2one('ir.model.fields', 'Field'),
		'predicate': fields.char('Predicate', size=256),
	}
nan_semantic_ontology()

