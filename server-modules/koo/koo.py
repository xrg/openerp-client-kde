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
from osv import orm
import SimpleXMLRPCServer
import re
from service import security
import netsvc
import sql_db
import pooler
import operator

class ir_attachment(osv.osv):
	_name = 'ir.attachment'
	_inherit = 'ir.attachment'

	def _all_models(self, cr, uid, context={}):
                ids = self.pool.get('ir.model').search(cr, uid, [], context=context)
                data = self.pool.get('ir.model').read(cr, uid, ids, ['model','name'])
                return [(x['model'], x['name']) for x in data]


	def _record(self, cr, uid, ids, field_name, arg, context={}):
		res = {}
		for record in self.browse(cr, uid, ids):
			res[ record.id ] = '%s,%d' % (record.res_model, record.res_id)
		return res

	_columns = {
		'record': fields.function(_record, method=True, string='Record', type='reference', selection=_all_models)
	}
ir_attachment()

regex_order = re.compile('^(([a-z0-9_]+|"[a-z0-9_]+")( *desc| *asc)?( *, *|))+$', re.I)

class koo_services(netsvc.Service):
	def __init__(self, name='koo'):
		netsvc.Service.__init__(self,name)
		self.joinGroup('web-services')
		self.exportMethod(self.search)

	def search(self, db, uid, passwd, model, filter, offset=0, limit=None, order=None, context=None, count=False):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		pool = pooler.get_pool(db)
		if not context:
			context = {}

		# Check to avoid SQL injection later
		model = pool.get(model)._name
		table = pool.get(model)._table

		# compute the where, order by, limit and offset clauses
		(qu1, qu2, tables) = pool.get(model)._where_calc(cr, uid, filter, context=context)

		if len(qu1):
		    qu1 = ' where ' + ' and '.join(qu1)
		else:
		    qu1 = ''

		resortField = False
		resortOrder = False
		if order:
		    pool.get(model)._check_qorder(order)
		    m = regex_order.match( order )
		    field = m.group(2)
		    if field in pool.get(model)._columns:
		    	if isinstance( pool.get(model)._columns[field], fields.many2one ):
				# USING STANDARD search() FUNCTION
				#resortField = field
				#if m.group(3).strip().upper() in ('ASC', 'DESC'):
					#resortOrder = m.group(3)
				
				# DIRECT JOIN WITH NO TRANSLATION SUPPORT
				obj = pool.get(model)._columns[field]._obj
				rec_name = pool.get(obj)._rec_name
				obj = pool.get(obj)._table
				t = tables[0]
				tables[0] = '(%s LEFT JOIN (SELECT id AS join_identifier, "%s" AS join_sort_field FROM "%s") AS left_join_subquery ON %s = join_identifier) AS %s' % (t, rec_name, obj, field, t) 
				order = 'join_sort_field'
				if m.group(3).strip().upper() in ('ASC', 'DESC'):
					order += m.group(3)

		order_by = order or pool.get(model)._order

		limit_str = limit and ' limit %d' % limit or ''
		offset_str = offset and ' offset %d' % offset or ''


		# construct a clause for the rules :
		d1, d2 = pool.get('ir.rule').domain_get(cr, uid, model)
		if d1:
		    qu1 = qu1 and qu1+' and '+d1 or ' where '+d1
		    qu2 += d2

		if count:
		    cr.execute('select count(%s.id) from ' % table +
			    ','.join(tables) +qu1 + limit_str + offset_str, qu2)
		    res = cr.fetchall()
		    return res[0][0]

		# execute the "main" query to fetch the ids we were searching for
		cr.execute('select %s.id from ' % table + ','.join(tables) +qu1+' order by '+order_by+limit_str+offset_str, qu2)
		res = [x[0] for x in cr.fetchall()]

		#if resortField:
		#	# This code tries to respect the order returned by standard search()
		#	# The problem is that it currently doesn't sort correctly in translatable
		#	# fields.
		#	obj = pool.get(model)._columns[resortField]._obj
		#	o = pool.get(obj)._rec_name or 'name'
		#	if resortOrder:
		#		o += resortOrder
		#	ids = pool.get(obj).search(cr, uid, filter, order=o, context=context)
		#	hash = {}
		#	for x in xrange(len(ids)):
		#		hash[ids[x]] = x
		#	data = []
		#	for record in pool.get(model).read(cr, uid, res, ['id', resortField], context=context):
		#		data.append( (record['id'], hash.get(record[resortField][0])) )
		#	data.sort(key=operator.itemgetter(1))
		#	res = [x[0] for x in data]

		return res
koo_services()
paths = list(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths) + ['/xmlrpc/koo' ]
SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths = tuple(paths)

class nan_koo_settings(osv.osv):
	_name = 'nan.koo.settings'

	def _check_limit(self, cr, uid, ids, context={}):
		for x in self.read(cr, uid, ids, ['limit']):
			if x['limit'] <= 0:
				return False
		return True

	def _check_interval(self, cr, uid, ids, context={}):
		for x in self.read(cr, uid, ids, ['requests_refresh_interval']):
			if x['requests_refresh_interval'] <= 0:
				return False
		return True

	_columns = {
		'name': fields.char( 'Settings Name', 50, required=True, help='Name to be given to these settings.' ),
		'show_toolbar': fields.boolean( 'Show toolbar', help='Whether toolbar is shown on screens. Note the toolbar may be convenient but not necessary as all options are available from the Reports, Actions, Browse and Plugins menu entries.' ),
		'tabs_position': fields.selection( [('left', 'Left'), ('top', 'Top'), 
			('right', 'Right'), ('bottom', 'Bottom')], 'Default tabs position', required=True, 
			help='Tabs can be on the left, top, right or bottom by default. Note that some screens may require an specific position which will override this default.' ),
		'tabs_closable': fields.boolean( 'Show Close Button on Tabs', help="A close button will be shown in each tab."),
		'stylesheet': fields.text( 'Stylesheet', help='A valid Qt Stylesheet can be provided to be applied once the user has logged in.' ),
		'sort_mode': fields.selection( [('visible_items', 'Visible Items'), ('all_items', 'All Items')], 'Sorting Mode', help='If set to "Visible Items" only the "Limit" elements are loaded and sorting is done in the client side. If "All Items" is used, sorting is done in the server and all records are (virtually) loaded in chunks of size "Limit"'),
		'limit': fields.integer('Limit',help='Number of records to be fetched at once.'),
		'requests_refresh_interval': fields.integer('Requests refresh interval (seconds)', help='Indicates the number of seconds to wait to check if new requests have been received by the current user.'),
		'show_system_tray_icon': fields.boolean( 'Show Icon in System Tray', help='If checked, an icon is shown in the system tray to keep Koo accessible all the time.' ),
		'roles_id': fields.many2many('res.roles', 'nan_koo_settings_roles_rel', 'setting_id', 'role_id', 'Roles', help='Roles to which these settings apply.'),
		'print_directly': fields.boolean( 'Print directly', help='If set, sends the document directly to the printer. Otherwise the document is shown in a PDF viewer.' ),
		'auto_reload': fields.boolean( 'Auto Reload', help='If set, all views will be reloaded when data changes in the server.' ),
		'allow_massive_updates': fields.boolean( 'Allow Massive Updates', help='If set, the option to Modify all Selected Records is enabled in Form menu.' ),
		'attachments_dialog': fields.boolean( 'Attachments in a Dialog', help="If set, pushing on attachments button will open them in a new blocking dialog. Otherwise they will be opened in a new tab" ),
		'use_cache': fields.boolean('Allow Client Caching', help="If set, it enables the caching mechanism of the client. Developers will often consider disabling this option so they avoid clicking Clear Cache after changing views and actions."),
		'auto_new': fields.boolean('Automatically create new record', help="If set, it will put the user in a new document just after saving a new document. This eases creation of many records. Resembles old (4.2) behaviour of the application."),
	}
	_defaults = {
		'limit': lambda *a: 80,
		'requests_refresh_interval': lambda *a: 300,
		'use_cache': lambda *a: True,
	}
	_constraints = [
		(_check_limit, 'Limit must be greater than zero.', ['limit']),
		(_check_interval, 'Requests refresh interval must be greater than zero.', ['requests_refresh_interval']),
	]
	

	# Returns the id of the settings to load. Currently only uses roles to
	# decide the appropiate settings, but in the future it could use user IP
	# address or other supplied parameters.
	def get_settings_id(self, cr, uid):
		user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
		ids = [x.id for x in user.roles_id]
		if not ids:
			return False
		ids = str(ids).replace('[', '(').replace(']',')')
		cr.execute( "SELECT setting_id FROM nan_koo_settings_roles_rel WHERE role_id IN %s" % ( ids ) )
		row = cr.fetchone()
		if row:
			return row[0]
		else:
			return False

	def get_settings(self, cr, uid):
		ids = self.pool.get('nan.koo.cache.exception').search(cr, uid, [])
		exceptions = []
		for exception in self.pool.get('nan.koo.cache.exception').browse(cr, uid, ids):
			exceptions.append( exception.name )

		settings = {
			'cache_exceptions': exceptions
		}
		id = self.get_settings_id(cr, uid)
		if id:
			settings.update( self.read(cr, uid, [id])[0] )
		return settings
		
nan_koo_settings()

class nan_koo_view_settings(osv.osv):
	_name = 'nan.koo.view.settings'
	_columns = {
		'user': fields.many2one('res.users', 'User'),
		'view': fields.many2one('ir.ui.view', 'View'),
		'data': fields.text('Data')
	}
nan_koo_view_settings()

class nan_koo_cache_exceptions(osv.osv):
	_name = 'nan.koo.cache.exception'
	_columns = {
		'name': fields.char('Model Name', size=64, required=True),
	}
nan_koo_cache_exceptions()


# Workaround to 5.0 server regression. Since recent revisions they have introduced
# a get_server_enviroment() function which takes a lot of time and thus we need to 
# know on the client whether the field is sortable or not before trying.
#
# This function adds the 'stored' attribute to all fields, in case the server is
# not ready to do so. A patch has been sent, but we already have this in case it's
# not accepted or it takes a long time.

import osv.orm

old_fields_get = osv.orm.orm_template.fields_get

def new_fields_get(self, cr, user, fields=None, context=None, read_access=True):
	res = old_fields_get(self, cr, user, fields, context, read_access)
	# Return wether the field is stored in the database or not,
	# so the client can decide if it can be sorted.
	for f in res.keys():
		if not f in self._columns:
			continue
		if hasattr(self._columns[f], 'store'):
			if self._columns[f].store:
				res[f]['stored'] = True
			else:
				res[f]['stored'] = False
		else:
			res[f]['stored'] = True
	return res

osv.orm.orm_template.fields_get = new_fields_get


# Hack to return all actions in fields_view_get

old_fields_view_get = osv.orm.orm_template.fields_view_get

def new_fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False):
	result = old_fields_view_get( self, cr, user, view_id, view_type, context, toolbar )
	if toolbar:
		def clean(x):
			x = x[2]
			for key in ('report_sxw_content', 'report_rml_content',
				'report_sxw', 'report_rml',
				'report_sxw_content_data', 'report_rml_content_data'):
				if key in x:
					del x[key]
			return x

		ir_values_obj = self.pool.get('ir.values')
		resprint = ir_values_obj.get(cr, user, 'action', 'client_print_multi', 
			[(self._name, False)], False, context)
		resaction = ir_values_obj.get(cr, user, 'action', 'client_action_multi', 
			[(self._name, False)], False, context)
		resrelate = ir_values_obj.get(cr, user, 'action', 'client_action_relate', 
			[(self._name, False)], False, context)
		resprint = map(clean, resprint)
		resaction = map(clean, resaction)
		# Standard fields_view_get function returns only those actions with multi==False.
		#resaction = filter(lambda x: not x.get('multi', False), resaction)
		#resprint = filter(lambda x: not x.get('multi', False), resprint)
		resrelate = [x[2] for x in resrelate]

		for x in resprint + resaction + resrelate:
			x['string'] = x['name']

		result['toolbar'] = {
			'print': resprint,
			'action': resaction,
			'relate': resrelate
		}
	return result

osv.orm.orm_template.fields_view_get = new_fields_view_get
