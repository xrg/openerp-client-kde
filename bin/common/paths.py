import os
import sys

def searchFile(file, subdir=None):
	tests = []
	if subdir:
		tests += [os.path.join( x, subdir ) for x in sys.path]
		# The following line is needed for KTiny to work properly
		# under windows. Mainly we say attach 'share/ktiny/subdir' to
		# sys.path, which by default has 'c:\python25' (among others). 
		# This will give 'c:\python25\share\ktiny\ui' for example, which is 
		# where '.ui' files are stored under the Windows platform.
		tests += [os.path.join( x, 'share', 'ktiny', subdir ) for x in sys.path]
	else:
		tests += sys.path
		
	for p in tests:
		x = os.path.join(p, file)
		if os.path.exists(x):
			return x
	return False

kPath = lambda x: searchFile(x)
uiPath = lambda x: searchFile(x, 'ui')

