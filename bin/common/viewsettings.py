#   Copyright (C) 2008 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or 
#   (at your option) any later version. 
#
#   This program is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License 
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 

import rpc 

# Settings are stored as a string (not unicode) and in most cases
# end up converted to/from a QByteArray; hence the need of ensuring
# we use str instead of unicode. That's why we enforce str() in a
# couple of places.
class ViewSettings:
	cache = {}
	databaseName = None
	uid = None
	hasSettingsModule = True

	# Gets a view and stores it's settings for the current user
	# @param view View object (should inherit AbstractView)
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

		# Add settings in the cache. Note that even if the required ktiny
		# module is not installed in the server view settings will be kept
		# during user session.
		ViewSettings.cache[id] = settings

		if not ViewSettings.hasSettingsModule:
			return
			
		try:
			# We don't want to crash if the ktiny module is not installed on the server
			# but we do want to crash if there are mistakes in setViewSettings() code.
			ids = rpc.session.call( '/object', 'execute', 'nan.ktiny.view.settings', 'search', [
				('user','=',rpc.session.uid),('view','=',id)
			])
		except:
			ViewSettings.hasSettingsModule = False
			return
		# As 'nan.ktiny.view.settings' is proved to exist we don't need try-except here. And we
		# can use execute() instead of call().
		if ids:
			rpc.session.execute( '/object', 'execute', 'nan.ktiny.view.settings', 'write', ids, {
				'data': settings 
			})
		else:
			rpc.session.execute( '/object', 'execute', 'nan.ktiny.view.settings', 'create', {
				'user': rpc.session.uid, 
				'view': id, 
				'data': settings 
			})

	@staticmethod
	def load( id ):
		if not id:
			return None

		ViewSettings.checkConnection()

		if id in ViewSettings.cache:
			# Restore settings from the cache. Note that even if the required ktiny
			# module is not installed in the server view settings will be kept
			# during user session.
			return ViewSettings.cache[id]

		if not ViewSettings.hasSettingsModule:
			return None

		try:
			# We don't want to crash if the ktiny module is not installed on the server
			# but we do want to crash if there are mistakes in setViewSettings() code.
			ids = rpc.session.call( '/object', 'execute', 'nan.ktiny.view.settings', 'search', [
				('user','=',rpc.session.uid),('view','=',id)
			])
		except:
			ViewSettings.hasSettingsModule = False
			return None
		# As 'nan.ktiny.view.settings' is proved to exist we don't need try-except here.
		if not ids:
			return None
		settings = rpc.session.execute( '/object', 'execute', 'nan.ktiny.view.settings', 'read', ids, ['data'] )[0]['data']

		if settings:
			# Ensure it's a string and not unicode
			settings = str(settings)

		ViewSettings.cache[id] = settings

		return settings

	# Checks if connection has changed and clears cache and hasSettingsModule flag
	@staticmethod
	def checkConnection():
		if ViewSettings.databaseName != rpc.session.databaseName or ViewSettings.uid != rpc.session.uid:
			ViewSettings.clear()

	# Clears cache and resets state. This means that after installing the ktiny
	# module you don't have to close session and login again because
	# hasSettingsModule is reset to True.
	@staticmethod
	def clear():
		ViewSettings.databaseName = rpc.session.databaseName
		ViewSettings.uid = rpc.session.uid
		ViewSettings.hasSettingsModule = True
		ViewSettings.cache = {}

