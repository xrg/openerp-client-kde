from service.http_server import reg_http_service, HttpDaemon
from service.websrv_lib import HTTPDir
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import netsvc
import tools

class Message:
    def __init__(self):
        self.status = False

class JasperHandler(netsvc.OpenERPDispatcher, BaseHTTPRequestHandler):
    cache = {}

    def __init__(self, request, client_address, server):
        pass
        #print "REQUEST: ", dir(request)
        #print "DIR SELF: ", dir(self)

    #def __getattr__(self, name):
        #print "NAME: ", name
        #return JasperHandler.__getattr__(self, name)

    def do_OPTIONS(self):
        pass

    def parse_request(self, *args, **kwargs):
        #self.headers = Message()
        #self.request_version = 'HTTP/1.1'
        #self.command = 'OPTIONS'

        path = self.raw_requestline.replace('GET','').strip().split(' ')[0]
        try:
            result = self.execute(path)
        except Exception, e:
            result = '<error><exception>%s</exception></error>' % (e.args, )
        self.wfile.write( result )
        return True

    def execute(self, path):
        #print "PATH: ", path
        path = path.strip('/')
        path = path.split('?')
        model = path[0]
        arguments = {}
        for argument in path[-1].split('&'):
            argument = argument.split('=')
            arguments[ argument[0] ] = argument[-1]

        use_cache = tools.config.get('jasper_cache', True)
        database = arguments.get('database', tools.config.get('jasper_database', 'demo') )
        user = arguments.get('user', tools.config.get('jasper_user', 'admin') )
        password = arguments.get('password', tools.config.get('jasper_password', 'admin') )
        depth = int( arguments.get('depth', tools.config.get('jasper_depth', 3) ) )
        language = arguments.get('language', tools.config.get('jasper_language', 'en'))

        # Check if data is in cache already
        key = '%s|%s|%s|%s|%s' % (model, database, user, depth, language)
        if key in self.cache:
            return self.cache[key]

        context = {
            'lang': language,
        }

        uid = self.dispatch('common', 'login', (database, user, password) )
        result = self.dispatch('object', 'execute', (database, uid, password, 'ir.actions.report.xml', 'create_xml', model, depth, context) )

        if use_cache:
            self.cache[key] = result

        return result

reg_http_service(HTTPDir('/jasper/', JasperHandler))
