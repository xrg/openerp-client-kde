##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#					Fabien Pinckaers <fp@tiny.Be>
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

import gettext

import rpc
import os
import sys
import logging
from options import options

import threading
import common

from PyQt4.QtCore  import  *
from PyQt4.QtGui import *
from PyQt4.uic import *

#
# Upgrade this number to force the client to ask the survey
#
SURVEY_VERSION = '0'

def _search_file(file, dir='path.share'):
	tests = [
		lambda x: os.path.join(options.options[dir],x),
		lambda x: os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), x),
		lambda x: os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'ui', x),
	]
	for func in tests:
		x = func(file)
		if os.path.exists(x):
			return x
	return False

kPath = lambda x: _search_file(x, 'path.share')
uiPath = lambda x: _search_file(x, 'path.ui')



# node_attributes(): Returns a dictionary with all the attributes found in a XML 
#  with their name as key and the corresponding value.
def node_attributes(node):
   result = {}
   attrs = node.attributes
   if attrs is None:
	return {}
   for i in range(attrs.length):
	result[attrs.item(i).localName] = attrs.item(i).nodeValue
   return result

class SelectionDialog(QDialog):	
	def __init__(self, title, values, alwaysask=False, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath( 'win_selection.ui' ), self )
		if title:
			self.uiTitle.setText( title )
		for x in values.keys():
			item = QListWidgetItem()
			item.setText(x)
			item.setData(Qt.UserRole, QVariant(values[x]))
			self.uiList.addItem( item )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.selected )

	def selected(self):
		self.result = ""
		item = self.uiList.currentItem()
		self.result = ( str(item.text()), str(item.data(Qt.UserRole).toString()) )
		self.accept()

def selection(title, values, alwaysask=False):
	if len(values) == 0:
		return None
	elif len(values)==1 and (not alwaysask):
		key = values.keys()[0]
		return (key, values[key])
	s = SelectionDialog(title, values, alwaysask)
	if s.exec_() == QDialog.Accepted:
		return s.result
	else:
		return False
	

## The TipOfTheDayDialog class shows a dialog with a Tip of the day
class TipOfTheDayDialog( QDialog ):
	# TODO: Use KTipDialog when we start using KDE libs
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		try:
			self.number = int(options.options['tip.position'])
		except:
			self.number = 0
			log = logging.getLogger('common.message')
			log.error('Invalid value for option tip.position ! See ~/.terprc !')
	
		loadUi( uiPath('tip.ui'), self )	
		self.connect( self.pushNext, SIGNAL('clicked()'), self.nextTip )
		self.connect( self.pushPrevious, SIGNAL('clicked()'), self.previousTip )
		self.connect( self.pushClose, SIGNAL('clicked()'), self.closeTip )
		self.uiShowNextTime.setChecked( options.options['tip.autostart'] )
		self.showTip()
	
	def showTip(self):
		tips = file(kPath('ktinytips.txt')).read().split('---')
		tip = tips[self.number % len(tips)]
		del tips
		self.uiTip.setText(tip)

	def nextTip(self):
		self.number+=1
		self.showTip()

	def previousTip(self):
		if self.number>0:
			self.number -= 1
		self.showTip()

	def closeTip(self):
		options.options['tip.autostart'] = self.uiShowNextTime.isChecked()
		options.options['tip.position'] = self.number+1
		options.save()
		self.close()

def upload_email(email):
	try:
		import urllib
		args = urllib.urlencode([('mail_subscribe',email),('subscribe','Subscribe')])
		fp = urllib.urlopen('http://tinyerp.com/index.html', args)
		fp.read()
		fp.close()
	except:
		pass
	return True

class upload_data_thread(threading.Thread):
	def __init__(self, email, data, type, supportid):
		self.args = [('email',email),('type',type),('supportid',supportid),('data',data)]
		super(upload_data_thread,self).__init__()
	def run(self):
		try:
			import urllib
			args = urllib.urlencode(self.args)
			fp = urllib.urlopen('http://tinyerp.com/scripts/survey.php', args)
			fp.read()
			fp.close()
		except:
			pass

def upload_data(email, data, type='survey2', supportid=''):
	a = upload_data_thread(email, data, type, supportid)
	a.start()

class terp_survey( QDialog ):
	
	def __init__( self ):	
		QDialog.__init__( self )
		win= loadUi( uiPath('survey.ui'), self )
		
		industry_list = QStringList()
		industry_list << '(choose one)'<< 'Apparel' << 'Banking' << 'Biotechnology' << 'Chemicals'<<'Communications'<<'Construction'<<'Consulting'<<'Education'<<'Electronics'<<'Energy'<<'Engineering'<<'Entertainment'<<'Environmental'<<'Finance'<<'Government'<<'Healthcare'<<'Hospitality'<<'Insurance'<<'Machinery'<<'Manufacturing'<<'Media'<<'Not For Profit'<<'Recreation'<<'Retail'<<'Shipping'<<'Technology'<<'Telecommunications'<<'Transportation'<<'Utilities'<<'Other'
		
		employee_list= QStringList()
		employee_list << '(choose one)'<< '0-5'<<'6-20'<<'21-50'<<'51-100'<<'101-250'<<'251-1000'<<'1001-2500'<<'2500+'
		role_list=QStringList()
		role_list << '(choose one)'<< 'Analyst'<<'Area Manager'<<'Chief Executive Off.'<<'Chief Financial Off.'<<'Chief HR Off.'<<'Chief Operating Off.' << 'Consultant'<<'Director'<<'Editor / Journalist'<<'Employee'<<'Executive Board' << 'Lecturer/University' << 'Manager'<< 'Project Manager'<<'Secretary'<<'Student'<<'System Admin.'<<'Other'
		
		country_list=QStringList()
		country_list << '(choose one)' << 'AALAND ISLANDS' << 'AFGHANISTAN' << 'ALBANIA'<<'ALGERIA'<<'AMERICAN SAMOA'<<'ANDORRA'<<'ANGOLA'<<'ANGUILLA'<<'ANTARCTICA'<<'ANTIGUA AND BARBUDA'<<'ARGENTINA'<<'ARMENIA'<<'ARUBA'<<'AUSTRALIA'<<'AUSTRIA'<<'AZERBAIJAN'<<'BAHAMAS'<<'BAHRAIN'<<'BANGLADESH'<<'BARBADOS'<<'BELARUS'<<'BELGIUM'<<'BELIZE'<<'BENIN'<<'BERMUDA'<<'BHUTAN'<<'BOLIVIA'<<'BOSNIA AND HERZEGOWINA'<<'BOTSWANA'<<'BOUVET ISLAND'<<'BRAZIL'<<'BRITISH INDIAN OCEAN'<<'TERRITORY'<<'BRUNEI DARUSSALAM'<<'BULGARIA'<<'BURKINA FASO'<<'BURUNDI'<<'CAMBODIA'<<'CAMEROON'<<'CANADA'<<'CAPE VERDE'<<'CAYMAN ISLANDS'<< 'CENTRAL AFRICAN REPUBLIC' << 'CHAD'<<'CHILE'<<'CHINA'<<'CHRISTMAS ISLAND'<<'COCOS (KEELING) ISLANDS'<<'COLOMBIA'<<'COMOROS'<<'CONGO'<<'COOK ISLANDS'<<'COSTA RICA'<<"COTE D'IVOIRE"<<'CROATIA'<<'CUBA'<<'CYPRUS'<<'CZECH REPUBLIC'<<'DENMARK'<<'DJIBOUTI'<<'DOMINICA'<<'DOMINICAN REPUBLIC'<<'ECUADOR'<<'EGYPT'<<'EL SALVADOR'<<'EQUATORIAL GUINEA'<<'ERITREA'<< 'ESTONIA'<<'ETHIOPIA'<<'FALKLAND ISLANDS (MALVINAS)'<<'FAROE ISLANDS'<<'FIJI'<<'FINLAND'<<'FRANCE'<<'FRENCH GUIANA'<<' FRENCH POLYNESIA'<<'FRENCH SOUTHERN TERRITORIES'<<'GABON'<<'GAMBIA'<<'GEORGIA'<<'GERMANY'<<'GHANA'<<'GIBRALTAR'<<'GREECE'<<'GREENLAND'<<'GRENADA'<<'GUADELOUPE'<<'GUAM'<<'GUATEMALA'<<'GUINEA'<<'GUINEA-BISSAU'<<'GUYANA'<<'HAITI'<<'HEARD AND MC DONALD ISLANDS'<<'HONDURAS'<<'HONG KONG'<<'HUNGARY'<<'ICELAND'<<'INDIA'<<'INDONESIA'<<'IRAN'<<'IRAQ'<<'IRELAND'<<'ISRAEL'<<'ITALY'<<'JAMAICA'<<'JAPAN'<<'JORDAN'<<'KAZAKHSTAN'<<'KENYA'<<'KIRIBATI'<<'KOREA'<<'KUWAIT'<<'KYRGYZSTAN'<<'LAO'<<'LATVIA'<<'LEBANON'<<'LESOTHO'<<'LIBERIA'<<'LIBYAN ARAB JAMAHIRIYA'<<'LIECHTENSTEIN'<<'LITHUANIA'<<'LUXEMBOURG'<<'MACAU'<<'MACEDONIA'<<'MADAGASCAR'<<'MALAWI'<<'MALAYSIA'<<'MALDIVES'<<'MALI'<<'MALTA'<<'MARSHALLISLANDS'<<'MARTINIQUE'<<'MAURITANIA'<<'MAURITIUS'<<'MAYOTTE'<<'MEXICO'<<'MICRONESIA'<<'MOLDOVA'<<'MONACO'<<'MONGOLIA'<<'MONTSERRAT'<<'MOROCCO'<<'MOZAMBIQUE'<<'MYANMAR'<<'NAMIBIA'<<'NAURU'<<'NEPAL'<<'NETHERLANDS'<<'NETHERLANDS ANTILLES' <<'NEW CALEDONIA'<<'NEW ZEALAND'<<'NICARAGUA'<<'NIGER'<<'NIGERIA'<<'NIUE'<<'NORFOLK ISLAND'<<'NORTHERN MARIANA ISLANDS'<<'NORWAY'<<'OMAN'<<'PAKISTAN'<<'PALAU'<<'PANAMA'<<'PAPUA NEW GUINEA'<<'PARAGUAY'<<'PERU'<<'PHILIPPINES'<<'PITCAIRPITCAIRN'<<'POLAND'<<'PORTUGAL'<<'PUERTO RICO'<<'QATAR'<<'REUNION'<<'ROMANIA'<<'RUSSIAN FEDERATION'<<'RWANDA'<<'SAINT HELENA'<<'SAINT KITTS AND NEVIS'<<'SAINT LUCIA'<<'SAINT PIERRE AND MIQUELON'<<'SAINT VINCENT AND THE GRENADINES'<<'SAMOA'<<'SAN MARINO'<<'SAO TOME AND PRINCIPE'<<'SAUDI ARABIA'<<'SENEGAL'<<'SERBIA AND MONTENEGRO'<<'SEYCHELLES'<<'SIERRA LEONE'<<'SINGAPORE'<<'SLOVAKIA'<<'SLOVENIA'<<'SOLOMON ISLANDS'<<'SOMALIA'<<'SOUTH AFRICA'<<'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS'<<'SPAIN'<<'SRI LANKA'<<'SUDAN'<<'SURINAME'<<'SVALBARD AND JAN MAYEN ISLANDS'<<'SWAZILAND'<<'SWEDEN'<<'SWITZERLAND'<<'SYRIAN ARAB REPUBLIC'<<'TAIWAN'<<'TAJIKISTAN'<<'TANZANIA'<<'POLAND'<<'PORTUGAL'<<'PUERTO RICO'<<'QATAR'<<'REUNION'<<'ROMANIA'<<'RUSSIAN FEDERATION'<<'RWANDA'<<'SAINT HELENA'<<'SAINT KITTS AND NEVIS'<<'SAINT LUCIA'<<'SAINT PIERRE AND MIQUELON'<<'SAINT VINCENT AND THE GRENADINES'<<'SAMOA'<<'SAN MARINO'<<'SAO TOME AND PRINCIPE'<<'SAUDI ARABIA'<<'SENEGAL'<<'SERBIA AND MONTENEGRO'<<'SEYCHELLES'<<'SIERRA LEONE'<<'SINGAPORE'<<'SLOVAKIA'<<'SLOVENIA'<<'SOLOMON ISLANDS'<<'SOMALIA'<<'SOUTH AFRICA'<<'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS'<<'SPAIN'<<'SRI LANKA'<<'SUDAN'<<'SURINAME'<<'SVALBARD AND JAN MAYEN ISLANDS'<<'SWAZILAND'<<'SWEDEN'<<'SWITZERLAND'<<'SYRIAN ARAB REPUBLIC'<<'TAIWAN'<<'TAJIKISTAN'<<'TANZANIA'<<'THAILAND'<<'TIMOR-LESTE'<<'TOGO'<<'TOKELAU'<<'TONGA'<<'TRINIDAD AND TOBAGO'<<'TUNISIA'<<'TURKEY'<<'TURKMENISTAN'<<'TURKS AND CAICOS ISLANDS'<<'TUVALU'<<'UGANDA'<<'UKRAINE'<<'UNITED ARAB EMIRATES'<<'UNITEDKINGDOM'<<'UNITED STATES'<<'URUGUAY'<<'UZBEKISTAN'<<'VANUATU'<<'VATICAN CITY STATE'<<'VENEZUELA'<<'VIET NAM'<<'VIRGIN ISLANDS'<<'WALLIS AND FUTUNAISLANDS'<<'WESTERN SAHARA'<<'YEMEN'<<'ZAMBIA'<<'ZIMBABWE'		
		
	
		hear_list=QStringList()
		hear_list << '(choose one)' << 'Search Engine' << 'From a Tiny ERP Partner' << 'Conference or Trade show' << 'Link in another website' << 'Word of mouth' << 'In the press' << 'Other'
		
		system_list=QStringList()
		system_list << '(choose one)' << 'Windows' << 'Linux' << "Other's"
		
		opensource_list=QStringList()
		opensource_list << '(choose one)' << 'I only use open source softwares' << 'I use some open source softwares' << 'I never used open source software'
		
		
		widnames = ('country','role','industry','employee','hear','system','opensource')
		for widname in widnames:
			param = eval( widname+'_list')
			f=eval(' self.combo_'+widname+'.addItems' )
			f(param)
				

	def isShown( self ):
		if options.options['survey.position']==SURVEY_VERSION:
			return False
		else:
			options.options['survey.position']=SURVEY_VERSION
			options.save()
			return True
	
	def slotSurveyOk( self ):
		widnames = ('country','role','industry','employee','hear','system','opensource')
		email = self.entry_email.displayText(  ) 
		if '@' in email:
				upload_email(email)
		result = {}
		
		for widname in widnames:
			result[widname] = eval( 'self.combo_'+widname+'.currentText()' ) 
						
		result['plan_use']=self.check_use.isChecked()
		result['plan_sell']=self.check_sell.isChecked()
		result['note']=self.text_comment.toPlainText()
		import pickle
		result_pick = pickle.dumps(str(result))	
		upload_data(email, result_pick, type='SURVEY '+str(SURVEY_VERSION))
		self.close()		


class SupportDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('support.ui'), self )
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.send )
		self.uiSupportContract.setText( options['support.support_id'] )

	def send(self):
		QMessageBox.information(self, '', _('Sending support requests is not available with the TinyERP KDE client'))

def support():
	dialog = SupportDialog()
	dialog.exec_()

class ErrorDialog( QDialog ):
	def __init__(self, title, message, details='', parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('error.ui'), self )
		self.connect( self.pushSend, SIGNAL('clicked()'), self.send )
		self.uiSupportContract.setText( options['support.support_id'] )
		self.uiDetails.setText( details )
		self.uiErrorInfo.setText( message )
		self.uiErrorTitle.setText( title )

	def send(self):
		QMessageBox.information(self, '', _('Sending support requests is not available with the TinyERP KDE client'))

def warning(title, message):
	QMessageBox(None, title, message)

def error(title, message, details=''):
	log = logging.getLogger('common.message')
	log.error('MSG %s: %s' % (str(message),details))
	dialog = ErrorDialog( str(title), str(message), str(details) )
	dialog.exec_()
		
def to_xml(s):
	return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

## @brief The ProgressDialog class shows a progress bar moving left and right until you stop it.
#
# To use it:
# 1) Create a dialog (eg. dlg = ProgressDialog(self))
# 2) Call the start function (eg. dlg.start() )
# 3) Call the stop function when the operation has finished (eg. dlg.stop() )
# Take into account that the dialog will only show after a couple of seconds. This way, it
# only appears on long running tasks.
class ProgressDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		loadUi( uiPath('progress.ui'), self )
		self.progressBar.setMinimum( 0 )
		self.progressBar.setMaximum( 0 )
		
	def start(self):
		self.timer = QTimer()
		self.connect( self.timer, SIGNAL('timeout()'), self.timeout )
		self.timer.start( 2000 )

	def timeout(self):
		self.timer.stop()
		self.show()
		
	def stop(self):
		self.timer.stop()
		self.accept()

