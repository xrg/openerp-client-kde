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

## @brief The Notifications module handles warning and error notifications that 
# some components might need to throw. 
#  
#  The mechanism allows KTiny components to be loosely coupled with whatever 
#  the application programmer wants to do in these cases.
#  The error and warning handlers should be registered:
#
#\code
#  def error(title, message, detail):
#	print "ERROR: Title: %s, Message: %s, Detail: %s" % (title, message, detail)
#  def warning(title, message):
#	print "WARNING: Title: %s, Message: %s, Detail: %s" % (title, message, detail)
#
#  Notifications.errorHandler = error
#  Notifications.warningHandler = warning 
#\endcode
#
#  This will make that any component that needs to notify an error using 
#  Notifications.notifyError(), the error() function will be called. The same 
#  for warnings.
#  
#  If no handler is specified the notification will be ignored. The KTiny 
#  application uses a special form for errors and a message box for warnings.

errorHandler = None
warningHandler = None
concurrencyErrorHandler = None
lostConnectionErrorHandler = None

## @brief Calls the function that has been registered to handle errors.
def notifyError(title, message, detail):
	if errorHandler:
		errorHandler(title, message, detail)

## @brief Calls the function that has been registered to handle warnings.
def notifyWarning(title, message):
	if warningHandler:
		warningHandler(title, message)

## @brief Calls the function that has been registered to handle concurrency errors.
def notifyConcurrencyError(model, id, context):
	if concurrencyErrorHandler:
		return concurrencyErrorHandler(model, id, context)

## @brief Calls the function that has been registered to handle lost connection errors.
def notifyLostConnection(count):
	if lostConnectionErrorHandler:
		return lostConnectionErrorHandler(count)
