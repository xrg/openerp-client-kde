##############################################################################
#
# Copyright (c) 2010 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
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

from PyQt4.QtCore import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.plasma import *
from PyKDE4.plasmascript import Runner

from Koo import Rpc
from Koo.Common.Settings import Settings
from Koo.Common import Localization

import os
import re
import math
import subprocess

class KooRunner(Runner):
	def __init__(self,parent,args = None):
		Runner.__init__(self, parent)
		self.actions = []

	def init(self):
		self.reloadConfiguration()
		ign = Plasma.RunnerContext.Types(Plasma.RunnerContext.Directory |
				                 Plasma.RunnerContext.File |
						 Plasma.RunnerContext.NetworkLocation |
						 Plasma.RunnerContext.Executable |
						 Plasma.RunnerContext.ShellCommand)
	        self.setIgnoredTypes(ign)
		description = i18n("Full Text Search in OpenERP");

		self.addSyntax(Plasma.RunnerSyntax("%s :q:" % self.prefix, description)) 
	        self.setSpeed(Plasma.AbstractRunner.NormalSpeed)
	        self.setPriority(Plasma.AbstractRunner.LowestPriority)
	        self.setHasRunOptions(False)

		self.stripTags = re.compile(r'<.*?>')


	def textToQuery(self, text):
		q = text.strip()
		return re.sub(' +', '|', q)

	def match(self, context):
		if not Rpc.session.logged():
			return 

		text = unicode( context.query() )

		if self.prefix:
			if not text.startswith(self.prefix):
				return
			text = text[len(self.prefix):]

		text = self.textToQuery(text)

		results = Rpc.session.call('/fulltextsearch', 'search', text, self.limit, 0, False, Rpc.session.context)
		for result in results:
			match = Plasma.QueryMatch(self.runner)
			match.setType(Plasma.QueryMatch.PossibleMatch)
			match.setIcon(KIcon('games-hint'))
			label = '%s: %s' % (result['model_label'], self.stripTags.sub('', result['headline']))
			label = label.replace('\n','')
			match.setText( label )
			match.setData( '%s:%s' % (result['model_name'], result['id'] ) )
			match.setId(QString())
			context.addMatch(text, match)

	def run(self, context, match):
		env = os.environ.copy()
		# Use environment variable to pass the URL so that user password is not 
		# visible when listing running processes.
		env['KOO_URL'] = self.url
		data = unicode( match.data().toString() ).split(':')
		command = ['sh', '/usr/bin/koo', '--database', self.database, '--open-model', data[0], '--open-id', data[1]]
		process = subprocess.Popen(command, env=env)

	def reloadConfiguration(self):
		Settings.loadFromFile()

		self.prefix = Settings.value('runner.prefix', '')
		self.limit = Settings.value('runner.max_results', 5)

		# If no 'runner' specific settings, use standard Koo defaults
		self.language = Settings.value('runner.language', Settings.value('client.language') )
		self.url = Settings.value('runner.url', Settings.value('login.url') )
		self.database = Settings.value('runner.db', Settings.value('login.db') )

		Localization.initializeTranslations(self.language)
		if not Rpc.session.login(self.url, self.database):
			print '### KooRunner: Could not log in.'

	def teardown(self):
		pass

	def prepare(self):
		pass

def CreateRunner(parent):
	return KooRunner(parent)
