##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import os, time, base64, datetime

import rpc

import wizard
import printer

from common import api
from common import common
from PyQt4.QtGui import *

def executeReport(name, data, context={}):
	datas = data.copy()
	ids = datas['ids']
	del datas['ids']
	if not ids:
		ids =  rpc.session.execute('/object', 'execute', datas['model'], 'search', [])
		if ids == []:
			QMessageBox.information( None, '', _('Nothing to print!'))
			return False
		datas['id'] = ids[0]
	try:
		ctx = rpc.session.context.copy()
		ctx.update(context)
		report_id = rpc.session.execute('/report', 'report', name, ids, datas, ctx)
		state = False
		attempt = 0
		while not state:
			val = rpc.session.execute('/report', 'report_get', report_id)
			state = val['state']
			if not state:
				time.sleep(1)
				attempt += 1
			if attempt>200:
				QMessageBox.information( None, '', _('Printing aborted, too long delay !'))
				return False
		printer.print_data(val)
	except rpc.RpcException, e:
		common.error(_('Error: ')+str(e.type), e.message, e.data)
	return True

def execute(act_id, datas, type=None, context={}):
	ctx = rpc.session.context.copy()
	ctx.update(context)
	if type==None:
		res = rpc.session.execute('/object', 'execute', 'ir.actions.actions', 'read', [act_id], ['type'], ctx)
		if not len(res):
			raise Exception, 'ActionNotFound'
		type=res[0]['type']
	res = rpc.session.execute('/object', 'execute', type, 'read', [act_id], False, ctx)[0]
	api.instance.executeAction(res,datas)

def executeAction(action, datas, context={}):
	if 'type' not in action:
		return
	if action['type']=='ir.actions.act_window':
		for key in ('res_id', 'res_model', 'view_type', 'view_mode',
				'limit', 'auto_refresh'):
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
		ctx = {'active_id': datas.get('id',False), 'active_ids': datas.get('ids',[])}
		#ctx.update(common.expr_eval(action.get('context','{}'), ctx.copy()))
		ctx.update(rpc.session.evaluateExpression(action.get('context','{}'), ctx.copy()) )
		ctx.update(context)

		a = ctx.copy()
		a['time'] = time
		a['datetime'] = datetime
		#domain = common.expr_eval(action['domain'], a)
		domain = rpc.session.evaluateExpression(action['domain'], a)

		if datas.get('domain', False):
			domain.append(datas['domain'])

		api.instance.createWindow( view_ids, datas['res_model'], datas['res_id'], domain,
				action['view_type'], datas.get('window',None), ctx,
				datas['view_mode'], name=action.get('name', False), autoReload=datas['auto_refresh']  )

		#for key in tools.expr_eval(action.get('context', '{}')).keys():
		#	del rpc.session.context[key]

	elif action['type']=='ir.actions.wizard':
		win=None
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		wizard.execute(action['wiz_name'], datas, parent=win, context=context)

	elif action['type']=='ir.actions.report.custom':
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		datas['report_id'] = action['report_id']
		api.instance.executeReport('custom', datas)

	elif action['type']=='ir.actions.report.xml':
		if 'window' in datas:
			win=datas['window']
			del datas['window']
		api.instance.executeReport(action['report_name'], datas)

def executeKeyword(keyword, data={}, context={}):
	actions = None
	if 'id' in data:
		try:
			id = data.get('id', False) 
			actions = rpc.session.execute('/object', 'execute',
					'ir.values', 'get', 'action', keyword,
					[(data['model'], id)], False, rpc.session.context)
			actions = map(lambda x: x[2], actions)
		except rpc.RpcException, e:
			return False

	keyact = {}
	for action in actions:
		keyact[action['name']] = action

	res = common.selection(_('Select your action'), keyact)
	if res:
		(name,action) = res
		api.instance.executeAction(action, data, context=context)
		return (name, action)
	elif not len(keyact):
		QMessageBox.information( None, '', _('No action defined!'))
	return False

