class TinyApi:
	def execute(self, actionId, data={}, type=None, context={}):
		pass

	def executeReport(self, name, data={}, context={}):
		return True

	def executeAction(self, action, data={}, context={}):
		pass
		
	def executeKeyword(self, keyword, data={}, context={}):
		return False

	def createWindow(self, view_ids, model, res_id=False, domain=None, 
			view_type='form', window=None, context=None, mode=None, name=False, autoReload=False):
		pass

	def windowCreated(self, window):
		pass

# This variable should point to a TinyApi instance
instance = None
