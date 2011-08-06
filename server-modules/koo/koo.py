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
import release

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

if release.major_version == '5.0':
	netsvc_service = netsvc.Service
else:
	import service
	netsvc_service = service.web_services._ObjectService

class koo_services(netsvc_service):
	def __init__(self, name='koo'):
		netsvc_service.__init__(self,name)
		self.joinGroup('web-services')

		if release.major_version == '5.0':
			self.exportMethod(self.search)
		else:
			self.exportedMethods = [
				'search',
			]

	def dispatch(self, method, auth, params):
		if not method in self.exportedMethods:
			raise KeyError("Method not found: %s" % method)
		return self.common_dispatch(method, auth, params)

	def search(self, db, uid, passwd, model, filter, offset=0, limit=None, order=None, context=None, count=False, group=False):
		security.check(db, uid, passwd)
		conn = sql_db.db_connect(db)
		cr = conn.cursor()
		try:
			return self.exp_search(cr, uid, model, filter, offset, limit, order, context, count, group)
		finally:
			cr.close()

	def exp_search(self, cr, uid, model, filter, offset=0, limit=None, order=None, context=None, count=False, group=False):

		pool = pooler.get_pool(cr.dbname)
		if not context:
			context = {}

		# Check to avoid SQL injection later
		model = pool.get(model)._name
		table = pool.get(model)._table

		# compute the where, order by, limit and offset clauses
		if release.major_Version == '5.0':
			(qu1, qu2, tables) = pool.get(model)._where_calc(cr, uid, filter, context=context)
		else:
			query = pool.get(model)._where_calc(cr, uid, filter, context=context)
			qu1 = query.where_clause
			qu2 = query.where_clause_params
			tables = query.tables
			
		if len(qu1):
		    qu1 = ' where ' + ' and '.join(qu1)
		else:
		    qu1 = ''

		resortField = False
		resortOrder = False
		if order:
		    pool.get(model)._check_qorder(order)
		    m = regex_order.match( order )
		    field = m.group(2).replace('"', '')
		    if field in pool.get(model)._columns:
		    	if isinstance( pool.get(model)._columns[field], fields.many2one ):
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
		if group:
			cr.execute('select %s.id, %s from ' % (table, group) + ','.join(tables) +qu1+' order by '+order_by+limit_str+offset_str, qu2)
			res = []
			counter = 0 
			last_value = None
			for record in cr.fetchall():
				if last_value != x[1]:
					last_value = x[1]
					counter += 1
				res = [(x[0], counter)]
		else:
			cr.execute('select %s.id from ' % table + ','.join(tables) +qu1+' order by '+order_by+limit_str+offset_str, qu2)
			res = [x[0] for x in cr.fetchall()]

		return res

koo_services()
paths = list(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths) + ['/xmlrpc/koo' ]
SimpleXMLRPCServer.SimpleXMLRPCRequestHandler.rpc_paths = tuple(paths)

class nan_koo_release(osv.osv):
	_name = 'nan.koo.release'
	_rec_name = 'version'

	_columns = {
		'version': fields.char('Version', 20, required=True),
		'installer': fields.binary('Installer'),
		'filename': fields.char('File Name', 40, required=True),
		'command_line': fields.char('Command Line', 200, required=True, help='Command to be executed once the installer has been downloaded. "$path" may be used to refer to the directory where the file is stored. Example: $path\koo-setup-5.0.3.exe /S'),
		'release_notes': fields.text('Release Notes'),
		'platform': fields.selection([('nt','Windows'),('posix','Posix')], 'Platform', required=True),
		'downloads': fields.integer('Downloads', readonly=True, help='Number of times the installer has been downloaded.'),
	}
	_defaults = {
		'downloads': lambda *a: 0,
	}
	_sql_constraints = [
		('version_platform_uniq', 'unique(version, platform)', 'You can only have one installer per version and platform.'),
	]

	def needs_update(self, cr, uid, version, platform, download, context):
		ids = self.search(cr, uid, [
			('version','>',version),
			('platform','=',platform)
		], order='version DESC', limit=1, context=context)
		if not ids:
			return False
		release = self.browse(cr, uid, ids[0], context)
		if not release.installer:
			return False
		if download and release.installer:
			self.write(cr, uid, release.id, {
				'downloads': release.downloads + 1,
			}, context)
		return {
			'version': release.version,
			'release_notes': release.release_notes,
			'installer': download and release.installer or False,
			'filename': release.filename,
			'command_line': release.command_line,
		}

	def get_installer(self, cr, uid, version, platform, context):
		ids = self.search(cr, uid, [
			('version','=',version),
			('platform','=',platform)
		], context=context)
		if not ids:
			return False
		release = self.browse(cr, uid, ids[0], context)
		if release.installer:
			self.write(cr, uid, release.id, {
				'downloads': release.downloads + 1,
			}, context)
		return release.installer

nan_koo_release()


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
		'print_directly': fields.boolean( 'Print directly', help='If set, sends the document directly to the printer. Otherwise the document is shown in a PDF viewer.' ),
		'auto_reload': fields.boolean( 'Auto Reload', help='If set, all views will be reloaded when data changes in the server.' ),
		'allow_massive_updates': fields.boolean( 'Allow Massive Updates', help='If set, the option to Modify all Selected Records is enabled in Form menu.' ),
		'allow_import_export': fields.boolean('Allow import/export', help='If not set, it will not show the import/export options in the form menu.'),
		'attachments_dialog': fields.boolean( 'Attachments in a Dialog', help="If set, pushing on attachments button will open them in a new blocking dialog. Otherwise they will be opened in a new tab" ),
		'use_cache': fields.boolean('Allow Client Caching', help="If set, it enables the caching mechanism of the client. Developers will often consider disabling this option so they avoid clicking Clear Cache after changing views and actions."),
		'auto_new': fields.boolean('Automatically create new record', help="If set, it will put the user in a new document just after saving a new document. This eases creation of many records. Resembles old (4.2) behaviour of the application."),
		'load_on_open': fields.boolean('Load on Open', help="If set, it will load records the first time a view is opened. Otherwise, the user will have to search before anything is loaded. This may be interesting for performance reasons."),
		'fts_instant': fields.boolean('Instant Full Text Search', help="If set, full text search dialog will query the server after each key stroke, similar to what Google Instant does. Not recommended in databases with high load or lots of data in their full text search index."),
	}
	_defaults = {
		'show_toolbar': lambda *a: True,
		'tabs_position': lambda *a: 'top',
		'tabs_closable': lambda *a: True,
		'sort_mode': lambda *a: 'all_items',
		'limit': lambda *a: 80,
		'allow_massive_updates': lambda *a: True,
		'allow_import_export': lambda *a: True,
		'show_system_tray_icon': lambda *a: True,
		'requests_refresh_interval': lambda *a: 300,
		'use_cache': lambda *a: True,
		'load_on_open': lambda *a: True,
	}
	_constraints = [
		(_check_limit, 'Limit must be greater than zero.', ['limit']),
		(_check_interval, 'Requests refresh interval must be greater than zero.', ['requests_refresh_interval']),
	]
	

	# Returns the id of the settings to load. Currently only uses user ID to
	# decide the appropiate settings, but in the future it could use user IP
	# address or other supplied parameters.
	def get_settings_id(self, cr, uid):
		user = self.pool.get('res.users').browse(cr, uid, uid)
		return user.koo_settings_id and user.koo_settings_id.id

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

class res_users(osv.osv):
	_inherit = 'res.users'
	
	_columns = {
		'koo_settings_id': fields.many2one('nan.koo.settings', 'Koo Settings'),
	}
res_users()

class nan_koo_settings(osv.osv):
	_inherit = 'nan.koo.settings'
	_columns = {
		'user_ids': fields.one2many('res.users', 'koo_settings_id', 'Users'),
	}
nan_koo_settings()

class nan_koo_view_settings(osv.osv):
	_name = 'nan.koo.view.settings'
	_columns = {
		'user': fields.many2one('res.users', 'User'),
		'view': fields.many2one('ir.ui.view', 'View'),
		'model': fields.related('view', 'model', type='char', string='Model'),
		'data': fields.text('Data')
	}

	def name_get(self, cr, uid, ids, context=None):
		result = []
		for setting in self.browse(cr, uid, ids, context):
			result.append( (setting.id, '%s (%s)' % (settings.view.name, settings.user.name)) )
		return result

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

def new_fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
	if release.major_version == '5.0':
		result = old_fields_view_get( self, cr, user, view_id, view_type, context, toolbar )
	else:
		result = old_fields_view_get( self, cr, user, view_id, view_type, context, toolbar, submenu )
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

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
