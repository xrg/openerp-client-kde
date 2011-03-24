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

from osv import osv
from osv import fields

# This class holds the different priorities available
class priority(osv.osv):
	_name = 'fts.priority'
	_columns = {
		'name' : fields.char('Name', size=1),
		'value' : fields.float('Value (0-1.0)')
	}
priority()

# This class holds the indexes that we want to be created
# as soon as we execute the update index functions...
class full_text_index(osv.osv):
	_name = 'fts.full_text_index'
	_columns = {
		'field_id' : fields.many2one('ir.model.fields', 'Field', required=True, domain=[('ttype','in',['char','text','float','integer','date','datetime'])]),
		'priority' : fields.many2one('fts.priority', 'Priority', required=True),
		'model_id' : fields.related('field_id', 'model_id', type="many2one", relation='ir.model', string='Model', readonly=True)
	}
	_sql_constraints = [
		('field_id_uniq', 'unique(field_id)', 'You can only have one index entry per field.'),
	]

	def create(self, cr, uid, vals, context=None):
		id = vals['field_id']
		field = self.pool.get('ir.model.fields').browse(cr, uid, id, context)
		if field.name and field.model_id:
			# Recheck domain in case it was called from ir_model_fields
			if not field.ttype in ('char','text','float','integer','date','datetime'):
				raise osv.except_osv(_('Creation error'), _("Non indexable field type: '%s'") % field.name )
			column = self.pool.get(field.model_id.model)._columns[field.name]
			if isinstance( column, fields.function ) and not column.store: 
				raise osv.except_osv(_('Creation error'), _("Fields of type function can't be indexed: '%s'") % field.name )
		return super(full_text_index,self).create(cr, uid, vals, context)

	def write(self, cr, uid, ids, vals, context=None):
		if 'field_id' in vals:
			id = vals['field_id']
			field = self.pool.get('ir.model.fields').browse(cr, uid, id, context)
			# Recheck domain in case it was called from ir_model_fields
			if not field.ttype in ('char','text','float','integer','date','datetime'):
				raise osv.except_osv(_('Creation error'), _("Non indexable field type."))
			if field.name and field.model_id:
				column = self.pool.get(field.model_id.model)._columns[field.name]
				if isinstance( column, fields.function ) and not column.store: 
					raise osv.except_osv(_('Creation error'), _("Fields of type function can't be indexed: '%s'") % field.name )
		return super(full_text_index,self).write(cr, uid, ids, vals, context)

full_text_index()

# This class holds the indexes that are currently created
class current_full_text_index(osv.osv):
	_name = 'fts.current_full_text_index'
	_columns = {
		'field_id' : fields.many2one('ir.model.fields', 'Field', required=True),
		'priority' : fields.many2one('fts.priority', 'Priority', required=True),
		'model_id' : fields.related('field_id', 'model_id', type="many2one", relation='ir.model', string='Model', reaonly=True)
	}
current_full_text_index()

class ir_model_fields(osv.osv):
	_inherit = 'ir.model.fields'

	def _fts_priority(self, cr, uid, ids, name, arg, context=None):
		result = {}
		for id in ids:
			result[id] = False
		index_ids = self.pool.get('fts.full_text_index').search(cr, uid, [('field_id','in',ids)], context=context)
		for index in self.pool.get('fts.full_text_index').browse(cr, uid, index_ids, context):
			result[ index.field_id.id ] = index.priority.id
		return result

	def _set_fts_priority(self, cr, uid, id, field_name, value, args, context=None):
		index_ids = self.pool.get('fts.full_text_index').search(cr, uid, [('field_id','=',id)], context=context)
		if index_ids:
			if value:
				self.pool.get('fts.full_text_index').write(cr, uid, index_ids, {
					'priority': value,
				}, context)
			else:
				self.pool.get('fts.full_text_index').unlink(cr, uid, index_ids, context)
		elif value:
			self.pool.get('fts.full_text_index').create(cr, uid, {
				'field_id': id,
				'priority': value,
			}, context)
		return True

	def _fts_current_priority(self, cr, uid, ids, name, arg, context=None):
		result = {}
		for id in ids:
			result[id] = False
		index_ids = self.pool.get('fts.current_full_text_index').search(cr, uid, [('field_id','in',ids)], context=context)
		for index in self.pool.get('fts.current_full_text_index').browse(cr, uid, index_ids, context):
			result[ index.field_id.id ] = index.priority.id
		return result

	def write(self, cr, uid, ids, vals, context=None):
		if 'fts_priority' in vals:
			for id in ids:
				self._set_fts_priority(cr, uid, id, 'fts_priority', vals['fts_priority'], None, context)
			del vals['fts_priority']
		return super(ir_model_fields, self).write(cr, uid, ids, vals)
	

	_columns = {
		'fts_priority': fields.function(_fts_priority, fnct_inv=_set_fts_priority, method=True, type='many2one', relation='fts.priority', string='FTS Priority', help='Fields that should be indexed in the Full Text Search engine should be given a priority here.'),
		'fts_current_priority': fields.function(_fts_current_priority, method=True, type='many2one', relation='fts.priority', string='FTS Current Priority', help='Shows with which priority this field is being indexed at the moment. It may change after Update Full Text Index process.'),

		# Make 'select_level' field NOT required because many python fields do not have that value set anyway and this makes it impossible for users to change
		# FTS priority. The reason is that they're forced by the client to set a value in this field, but then write() raises an exception because the user is trying
		# to change a field that was created from python code.
		'select_level': fields.selection([('0','Not Searchable'),('1','Always Searchable'),('2','Advanced Search (deprecated)')],'Searchable', required=False),
	}
ir_model_fields()
