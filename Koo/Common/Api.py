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

## @brief KooApi class provides an interface several Koo components relay on being
# available for their proper use. 
class KooApi:
	## @brief Executes the given actionId (which can be a report, keword, etc.).
	def execute(self, actionId, data=None, type=None, context=None):
		pass

	## @brief Executes the server action to open a report.
	def executeReport(self, name, data=None, context=None):
		return True

	## @brief Executes the given server action (which can ba report, keyword, etc.).
	def executeAction(self, action, data=None, context=None):
		pass

	## @brief Executes the given server keyword action.
	def executeKeyword(self, keyword, data=None, context=None):
		return False

	## @brief Opens a new window (a new tab with Koo application) with the given model.
	def createWindow(self, view_ids, model, res_id=False, domain=None, 
			view_type='form', window=None, context=None, mode=None, name=False, autoReload=False,
			autoSearch=True,
			target='current'):
		pass

	## @brief Opens a new window (a new tab with Koo application) with the given url.
	def createWebWindow(self, url, title):
		pass

	## @brief This callback function is (should be) executed each time a new window (tab in Koo) is opened.
	def windowCreated(self, window, target):
		pass

# This variable should point to a KooApi instance
instance = None
