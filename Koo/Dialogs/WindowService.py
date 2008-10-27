##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

from Common import Api
from Common import Common
from FormWidget import *
from TreeWidget import *

import Rpc


def createWindow(view_ids, model, res_id=False, domain=None,
		view_type='form', window=None, context=None, mode=None, name=False, autoReload=False):

	if context is None:
		context = {}
	context.update(Rpc.session.context)

	if view_type=='form':
		mode = (mode or 'form,tree').split(',')
		win = FormWidget(model, res_id, domain, view_type=mode,
				view_ids = (view_ids or []), 
				context=context, name=name )
		win.setAutoReload( autoReload )
		Api.instance.windowCreated( win )
	elif view_type=='tree':
		if view_ids and view_ids[0]:
			view_base =  Rpc.session.execute('/object', 'execute',
					'ir.ui.view', 'read', [view_ids[0]],
					['model', 'type'], context)[0]
			model = view_base['model']
			view = Rpc.session.execute('/object', 'execute',
					view_base['model'], 'fields_view_get', view_ids[0],
					view_base['type'],context)
		else:
			view = Rpc.session.execute('/object', 'execute', model,
					'fields_view_get', False, view_type, context)

		win = TreeWidget(view, model, domain, context, name=name)
		Api.instance.windowCreated( win )
	else:
		import logging
		log = logging.getLogger('view')
		log.error('unknown view type: '+view_type)
		del log

