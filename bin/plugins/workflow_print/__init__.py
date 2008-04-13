from common import api
from common import common

def wkf_print(datas):
	datas['nested'] = True
	api.instance.executeReport('workflow.instance.graph', datas)
	return True

def wkf_print_simple(datas):
	datas['nested'] = False
	api.instance.executeReport('workflow.instance.graph', datas)
	return True
