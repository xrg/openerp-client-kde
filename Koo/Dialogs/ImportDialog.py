##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
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
from PyQt4.QtGui import *
from PyQt4.uic import *
import gettext
from Common import common

import Rpc

import csv, StringIO

from ImportExportCommon import *

def import_csv(csv_data, fields, model):
	fname = csv_data['fname']
	content = file(fname,'rb').read()
	input=StringIO.StringIO(content)
	data = list(csv.reader(input, quotechar=csv_data['del'], delimiter=csv_data['sep']))[int(csv_data['skip']):]
	datas = []
	for line in data:
		datas.append(map(lambda x:x.decode(csv_data['encoding']).encode('utf-8'), line))
	res = Rpc.session.execute('/object', 'execute', model, 'import_data', fields, datas)
	if res[0]>=0:
		QMessageBox.information( None, '', _('Imported %d objects !') % (res[0]))
	else:
		d = ''
		for key,val in res[1].items():
			d+= ('\t%s: %s\n' % (str(key),str(val)))
		error = _('Error trying to import this record:\n%(record)s\nError Message:\n%(error1)s\n\n%(error2)s') % {
			'record': d,
			'error1': res[2],
			'error2': res[3]
		}
		QMessageBox.warning(None, _('Error importing data'), error )

class ImportDialog(QDialog):
	def __init__(self, model, fields, preload = [], parent=None):
		QDialog.__init__(self, parent)
		loadUi(common.uiPath('win_import.ui'), self)
		self.model = model
		self.fields = fields
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		self.connect( self.pushAdd, SIGNAL('clicked()'), self.slotAdd )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.slotRemove )
		self.connect( self.pushRemoveAll, SIGNAL('clicked()'), self.slotRemoveAll )
		self.connect( self.pushAutoDetect, SIGNAL('clicked()'), self.slotAutoDetect )
		self.connect( self.pushOpenFile, SIGNAL('clicked()'), self.slotOpenFile )
		QTimer.singleShot( 0, self.initGui )

	def initGui(self):
		self.fieldsInfo = {}
		self.fieldsInvertedInfo = {}
		self.allModel = FieldsModel()
		self.setCursor( Qt.WaitCursor )
		self.allModel.load( self.fields, self.fieldsInfo, self.fieldsInvertedInfo )
		self.setCursor( Qt.ArrowCursor )
		self.uiAllFields.setModel( self.allModel )
		self.uiAllFields.sortByColumn( 0, Qt.AscendingOrder )

		self.selectedModel = FieldsModel()
		self.uiSelectedFields.setModel( self.selectedModel )

	def slotOpenFile(self):
		file = QFileDialog.getOpenFileName(self, _('File to import'))
		if file.isNull():
			return
		self.uiFileName.setText( file )

	def slotAccept(self):
		self.uiLinesToSkip.setValue(1)
		csv = {
			'fname': unicode(self.uiFileName.text()).strip(),
			'sep': unicode(self.uiFieldSeparator.text()).encode('ascii','ignore').strip(),
			'del': unicode(self.uiTextDelimiter.text()).encode('ascii','ignore').strip(),
			'skip': self.uiLinesToSkip.value(),
			'encoding': unicode(self.uiEncoding.currentText())
		}
		if csv['fname'] == '':
			QMessageBox.warning(self, _('Import error'), _('No file specified.'))
			return
		if len(csv['sep']) != 1:
			QMessageBox.warning(self, _('Import error'), _('Separator must be a single character.'))
			return
		if len(csv['del']) != 1:
			QMessageBox.warning(self, _('Import error'), _('Delimiter must be a single character.'))
			return
		fieldsData = []
		for x in range(0, self.selectedModel.rowCount() ):
			fieldsData.append( unicode( self.selectedModel.item( x ).data().toString() ) )

		if csv['fname']:
			import_csv(csv, fieldsData, self.model)
		self.accept()

	def slotAdd(self):
		idx = self.uiAllFields.selectionModel().selectedRows()
		if len(idx) != 1:
			return 
		idx = idx[0]
		item = self.allModel.itemFromIndex( idx )
		newItem = QStandardItem( item )
		newItem.setText( self.fullPathText(item) )
		newItem.setData( QVariant(self.fullPathData(item)) )
		self.selectedModel.appendRow( newItem )

	def slotRemove(self):
		idx = self.uiSelectedFields.selectedIndexes()
		if len(idx) != 1:
			return
		idx = idx[0]
		self.selectedModel.removeRows( idx.row(), 1 )

	def slotRemoveAll(self):
		if self.selectedModel.rowCount() > 0:
			self.selectedModel.removeRows(0, self.selectedModel.rowCount())

	def fullPathText(self, item):
		path = unicode( item.text() )
		while item.parent() != None:
			item = item.parent()
			path = item.text() + "/" + path
		return path

	def fullPathData(self, item):
		path = unicode( item.data().toString() )
		while item.parent() != None:
			item = item.parent()
			path = item.data().toString() + "/" + path
		return path

	def slotAutoDetect(self):
		fname=unicode(self.uiFileName.text())
		if not fname:
			QMessageBox.information(self, _('Auto-detect error'), 'You must select an import file first !')
			return 
		csvsep=unicode(self.uiFieldSeparator.text()).encode('ascii','ignore').strip()
		csvdel=unicode(self.uiTextDelimiter.text()).encode('ascii','ignore').strip()
		csvcode=unicode(self.uiEncoding.currentText()) or 'UTF-8'

		self.uiLinesToSkip.setValue(1)
		if len(csvsep) != 1:
			QMessageBox.warning(self, _('Auto-detect error'), _('Separator must be a single character.'))
			return
		if len(csvdel) != 1:
			QMessageBox.warning(self, _('Auto-detect error'), _('Delimiter must be a single character.'))
			return
		
		try:
			data = csv.reader(file(fname), quotechar=csvdel, delimiter=csvsep)
		except:
			QMessageBox.warning(self, _('Auto-detect error'), _('Error opening .CSV file: Input Error.') )
			return 
		self.slotRemoveAll()
		try:
			for line in data:
				for word in line:
					word=word.decode(csvcode).encode('utf-8')
					self.selectedModel.addField( word, self.fieldsInvertedInfo[word] )
				break
		except:
			QMessageBox.warning(self, _('Auto-detect error'), _('Error processing your first line of the file.\nField %s is unknown !') % (word) )

