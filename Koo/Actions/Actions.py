##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
# Copyright (C) 2011-2013 P. Christeas <xrg@hellug.gr>
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

import time

from Koo import Rpc

import Wizard
from Koo.Printer import *

from Koo.Common import Api
from Koo.Common import Common
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import logging

MAX_REPORT_ATTEMPTS = 200

class ExecuteReportThread(QThread):
	def __init__(self, name, data, context=None, parent=None):
		QThread.__init__(self, parent)
		if context is None:
			context = {}
		self.name = name
		self.datas = data.copy()
		self.context = context
		self.status = ''

	def run(self):
		ids = self.datas['ids']
		del self.datas['ids']
		if not ids:
			try:
				ids = Rpc.RpcProxy(self.datas['model']).search([],)
			except Rpc.RpcException, e:
				self.emit( SIGNAL('error'), ( _('Error: %s') % unicode(e.type), e.message, e.data ) )
				return
				
			if ids == []:
				self.emit( SIGNAL('warning'), _('Nothing to print.') )
				return 
			self.datas['id'] = ids[0]
		try:
			ctx = Rpc.session.context.copy()
			ctx.update(self.context)
			report_obj = Rpc.RpcCustomProxy('/report', auth_level='db', notify=True)
			report_id = report_obj.report(self.name, ids, self.datas, ctx)
			state = False
			attempt = 0
			while not state:
				val = report_obj.report_get(report_id)
				state = val['state']
				if not state:
					time.sleep(1)
					attempt += 1
				if attempt > MAX_REPORT_ATTEMPTS:
					self.emit( SIGNAL('warning'), _('Printing aborted. Delay too long.') )
					return False
			Printer.printData(val)
		except Rpc.RpcException, e:
			self.emit( SIGNAL('error'), ( _('Error: %s') % unicode(e.type), e.message, e.data ) )
		
## @brief Executes the given report.
def executeReport(name, data, context=None):
	if context is None:
		context = {}
	QApplication.setOverrideCursor( Qt.WaitCursor )
	datas = data.copy()
	ids = datas['ids']
	del datas['ids']
	try:
		if not ids:
			ids = Rpc.RpcProxy(datas['model']).search(datas.get('_domain',[]))
			if ids == []:
				QApplication.restoreOverrideCursor()
				QMessageBox.information( None, _('Information'), _('Nothing to print!'))
				return False
			datas['id'] = ids[0]
		ctx = Rpc.session.context.copy()
		ctx.update(context)
		report_obj = Rpc.RpcCustomProxy('/report', auth_level='db', notify=True)
		report_id = report_obj.report(name, ids, datas, ctx)
		state = False
		attempt = 0
		while not state:
			val = report_obj.report_get(report_id)
			state = val['state']
			if not state:
				time.sleep(1)
				attempt += 1
			if attempt > MAX_REPORT_ATTEMPTS:
				QApplication.restoreOverrideCursor()
				QMessageBox.information( None, _('Error'), _('Printing aborted, too long delay !'))
				return False
		Printer.printData(val, datas['model'], ids)
	except Rpc.RpcException, e:
		QApplication.restoreOverrideCursor()
		return False
	QApplication.restoreOverrideCursor()
	return True

## @brief Executes the given action id (it could be a report, wizard, etc).
def execute(act_id, datas, type=None, context=None):
	log = logging.getLogger('koo.action')
	if context is None:
		context = {}
	ctx = Rpc.session.context.copy()
	if context:
		ctx.update(context)
	log.debug("Context for action: %r" % ctx)
	if type==None:
		res = Rpc.RpcProxy('ir.actions.actions').read([act_id], ['type'], ctx)
		if not len(res):
			raise Exception, 'ActionNotFound'
		type=res[0]['type']
	res = Rpc.RpcProxy(type).read([act_id], False, ctx)[0]
	Api.instance.executeAction(res,datas,context)

## @brief Executes the given action (it could be a report, wizard, etc).
def executeAction(action, datas, context=None):
	log = logging.getLogger('koo.action')
	if context is None:
		context = {}
	if 'type' not in action:
		return
	
	ctx = context.copy()
	ctx.update({'active_id': datas.get('id',False), 'active_ids': datas.get('ids',[]),
                'active_model': datas.get('model',False)})
	log.debug('context for execAction (server): %r' % ctx)
	
	if action['type']=='ir.actions.act_window':
                for key in ('res_id', 'res_model', 'view_type', 'view_mode',
				'limit', 'auto_refresh', 'auto_search'):
			datas[key] = action.get(key, datas.get(key, None))

		if datas['limit'] is None or datas['limit'] == 0:
			datas['limit'] = 80

		view_ids=False
		if action.get('views', []):
			view_ids=[x[0] for x in action['views']]
			datas['view_mode']=",".join([x[1] for x in action['views']])
		elif action.get('view_id', False):
			view_ids=[action['view_id'][0]]

		if not action.get('domain', False):
			action['domain']='[]'

		try:
                    ctx_string = action.get('context','{}')
                    if ctx_string and ctx_string != '{}':
			# only at this type of action ?
			ctx.update(Rpc.session.evaluateExpression(ctx_string, ctx.copy()))
		except NameError,e:
			log.warn("Cannot evaluate context: %s" % e)
			log.debug('context for execAction 2: %r' % ctx)
			pass # ?
                
                # we don't expect ctx to be modified inside that eval!
		domain = Rpc.session.evaluateExpression(action['domain'], ctx)

		if datas.get('domain', False):
			domain.append(datas['domain'])

		target = action.get('target','current')
		if not target:
			target = 'current'
		Api.instance.createWindow( view_ids, datas['res_model'], datas['res_id'], domain,
			action['view_type'], datas.get('window',None), ctx,
			datas['view_mode'], name=action.get('name', False),
			autoSearch=datas.get('auto_search', True), autoReload=datas['auto_refresh'],
			target=target )

		#for key in tools.expr_eval(action.get('context', '{}')).keys():
		#	del Rpc.session.context[key]

	elif action['type']=='ir.actions.server':
		res = Rpc.RpcProxy('ir.actions.server').run([action['id']], ctx)
		if res:
			Api.instance.executeAction( res, datas, ctx )

	elif action['type']=='ir.actions.wizard':
		win=None
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		Wizard.execute(action['wiz_name'], datas, parent=win, context=context)

	elif action['type']=='ir.actions.report.custom':
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		datas['report_id'] = action['report_id']
		Api.instance.executeReport('custom', datas, ctx)

	elif action['type']=='ir.actions.report.xml':
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		datas.update( action.get('datas', {}) )
		Api.instance.executeReport(action['report_name'], datas, ctx)
	elif action['type']=='ir.actions.act_url':
		Api.instance.createWebWindow( action.get('url'), action.get('name') )

## @brief Executes the given keyword action (it could be a report, wizard, etc).
def executeKeyword(keyword, data=None, context=None):
	if data is None:
		data = {}
	if context is None:
		context = {}
	actions = None
	if 'id' in data:
		try:
			id = data.get('id', False) 
			actions = Rpc.RpcProxy('ir.values', notify=False).\
                                get('action', keyword, [(data['model'], id)],
                                    False, Rpc.session.context)
			if (actions):
				actions = map(lambda x: x[2], actions)
		except Rpc.RpcException, e:
			return None

	if not actions:
		return None

	keyact = {}
	for action in actions:
		keyact[action['name']] = action

	res = Common.selection(_('Select your action'), keyact)
	if not res:
		return None
	(name,action) = res
	Api.instance.executeAction(action, data, context=context)
	return (name, action)

#eof