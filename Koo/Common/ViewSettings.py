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

from Koo import Rpc 

## @brief ViewSettings class allows storing and retrieving of view state
# information such as column size and ordering in QListViews and the such.
#
# Settings are stored as a string (not unicode) and in most cases
# end up converted to/from a QByteArray; hence the need of ensuring
# we use str instead of unicode. That's why we enforce str() in a
# couple of places.
class ViewSettings:
	cache = {}
	databaseName = None
	uid = None
	hasSettingsModule = True

	## @brief Stores settings for the given view id.
	@staticmethod
	def store( id, settings ):
		if not id:
			return

		ViewSettings.checkConnection()

		if settings:
			# Ensure it's a string and not unicode
			settings = str(settings)

		# Do not update store data in the server if it settings have not changed
		# from the ones in cache.
		if id in ViewSettings.cache and ViewSettings.cache[id] == settings:
			return

		# Add settings in the cache. Note that even if the required koo
		# module is not installed in the server view settings will be kept
		# during user session.
		ViewSettings.cache[id] = settings

		if not ViewSettings.hasSettingsModule:
			return
			

		try:
                        settings_obj = Rpc.RpcProxy('nan.koo.view.settings', notify=False)
			# We don't want to crash if the koo module is not installed on the server
			# but we do want to crash if there are mistakes in setViewSettings() code.
			ids = settings_obj.search([('user','=',Rpc.session.get_uid()),('view','=',id) ])
			settings_obj.notify = True
		except Rpc.RpcServerException:
			ViewSettings.hasSettingsModule = False
			return
		# As 'nan.koo.view.settings' is proved to exist we don't need try-except here. And we
		# can use execute() instead of call().
		if ids:
			settings_obj.write(ids, { 'data': settings })
		else:
			settings_obj.create({ 'user': Rpc.session.get_uid(),
				'view': id,
				'data': settings,
                                })

	## @brief Loads information for the given view id.
	@staticmethod
	def load( id ):
		if not id:
			return None

		ViewSettings.checkConnection()
		if id in ViewSettings.cache:
			# Restore settings from the cache. Note that even if the required koo
			# module is not installed in the server view settings will be kept
			# during user session.
			return ViewSettings.cache[id]

		if not ViewSettings.hasSettingsModule:
			return None

		try:
			# We don't want to crash if the koo module is not installed on the server
			# but we do want to crash if there are mistakes in setViewSettings() code.
			settings_obj = Rpc.RpcProxy('nan.koo.view.settings', notify=False)
			
			ids = settings_obj.search([ ('user','=',Rpc.session.get_uid()),('view','=',id) ])
			settings_obj.notify = True
		except Rpc.RpcServerException:
			ViewSettings.hasSettingsModule = False
			return None

		# As 'nan.koo.view.settings' is proved to exist we don't need try-except here.
		if not ids:
			ViewSettings.cache[id] = None
			return None
		settings = settings_obj.read(ids, ['data'] )[0]['data']

		if settings:
			# Ensure it's a string and not unicode
			settings = str(settings)

		ViewSettings.cache[id] = settings

		return settings

	## @brief Checks if connection has changed and clears cache and hasSettingsModule flag
	@staticmethod
	def checkConnection():
		if ViewSettings.databaseName != Rpc.session.get_dbname() or ViewSettings.uid != Rpc.session.get_uid():
			ViewSettings.clear()

	## @brief Clears cache and resets state. This means that after installing the koo
	# module you don't have to close session and login again because
	# hasSettingsModule is reset to True.
	@staticmethod
	def clear():
		ViewSettings.databaseName = Rpc.session.get_dbname()
		ViewSettings.uid = Rpc.session.get_uid()
		ViewSettings.hasSettingsModule = True
		ViewSettings.cache = {}

#eof