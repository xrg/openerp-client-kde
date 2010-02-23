##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from Koo.Common import Api
from Koo.Common import Common
from Koo.Plugins import Plugins

## @brief Executes the workflow graph report 'workflow.instance.graph'
# including subworkflows.
def printWorkflow(model, id, ids, context):
	# Plugins might be called with no record selected but that doesn't
	# make sense for this plugin so simply return.
	if not id:
		return
	Api.instance.executeReport('workflow.instance.graph', {
		'id' : id,
		'ids' : ids,
		'model' : model,
		'nested' : True,
	}, context=context)

## @brief Executes the workflow graph report 'workflow.instance.graph' without
# subworkflows.
def printSimpleWorkflow(model, id, ids, context):
	# Plugins might be called with no record selected but that doesn't
	# make sense for this plugin so simply return.
	if not id:
		return
	Api.instance.executeReport('workflow.instance.graph', {
		'id' : id,
		'ids' : ids,
		'model' : model,
		'nested' : False,
	}, context=context)

Plugins.register( 'SimpleWorkflowPrinter', '.*', _('Print Workflow'), printSimpleWorkflow )
Plugins.register( 'WorkflowPrinter', '.*', _('Print Workflow (Complex)'), printWorkflow )
