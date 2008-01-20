from osv import osv, fields

# This class holds the different priorities available
class priority(osv.osv):
	_name = 'fts.priority'
	_columns = {
		'name' : fields.char('Name', size=1),
		'value' : fields.float('Value (0-1.0)')
	}
priority()

# This class defines all full text search (TSearch) configurations available
# There can be configurations for strings and numbers, for example. Or different languages.
class configuration(osv.osv):
	_name = 'fts.configuration'
	_columns = {
		'name' : fields.char('Name', size=64)
	}
configuration()

# This class holds the indexes that we want to be created
# as soon as we execute the update index functions...
class full_text_index(osv.osv):
	_name = 'fts.full_text_index'
	_columns = {
		'field_id' : fields.many2one('ir.model.fields', 'Field', required=True),
		'priority' : fields.many2one('fts.priority', 'Priority', required=True),
		'configuration' : fields.many2one('fts.configuration', 'Configuration', required=True)
	}
full_text_index()

# This class holds the indexes that are currently created
class current_full_text_index(osv.osv):
	_name = 'fts.current_full_text_index'
	_columns = {
		'field_id' : fields.many2one('ir.model.fields', 'Field', required=True),
		'priority' : fields.many2one('fts.priority', 'Priority', required=True),
		'configuration' : fields.many2one('fts.configuration', 'Configuration', required=True)
	}
current_full_text_index()

