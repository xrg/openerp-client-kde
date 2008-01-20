## The Notifications class handles warning and error notifications that some
#  components might need to throw. 
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

## Calls the function that has been registered to handle errors.
def notifyError(title, message, detail):
	if errorHandler:
		errorHandler(title, message, detail)

## Calls the function that has been registered to handle warnings.
def notifyWarning(title, message):
	if warningHandler:
		warningHandler(title, message)


