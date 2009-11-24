import os
import glob
import time
import socket
import subprocess
import xmlrpclib

class JasperServer:
	def __init__(self):
		self.proxy = xmlrpclib.ServerProxy( 'http://localhost:8090', allow_none = True )

	def path(self):
		return os.path.abspath(os.path.dirname(__file__))

	def start(self):
		env = {}
		env.update( os.environ )
		libs = os.path.join( self.path(), '..', 'java', 'lib', '*.jar' )
		env['CLASSPATH'] = os.path.join( self.path(), '..', 'java:' ) + ':'.join( glob.glob( libs ) ) + ':' + os.path.join( self.path(), '..', 'custom_reports' )
		os.spawnlpe(os.P_NOWAIT, 'java', 'java', 'com.nantic.jasperreports.JasperServer', env)

	def execute(self, *args):
		try: 
			self.proxy.Report.execute( *args )
		except (xmlrpclib.ProtocolError, socket.error), e:
			print "FIRST TRY DIDN'T WORK: ", str(e), str(e.args)
			self.start()
			for x in xrange(40):
				time.sleep(1)
				try:
					print "TRYING"
					return self.proxy.Report.execute( *args )
				except (xmlrpclib.ProtocolError, socket.error), e:
					print "EXCEPTION: ", str(e), str(e.args)
					pass

