import os
import sys

def searchFile(file, subdir=None):
	tests = []
	if subdir:
		tests += [os.path.join( x, subdir ) for x in sys.path]
	else:
		tests += sys.path
		
	for p in tests:
		x = os.path.join(p, file)
		if os.path.exists(x):
			return x
	return False

kPath = lambda x: searchFile(x)
uiPath = lambda x: searchFile(x, 'ui')

