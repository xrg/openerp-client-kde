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
from Koo.Common import Common
from Koo.Screen.ViewQueue import *

from Koo import Rpc

import csv
import StringIO

try:
	import xlrd
	isXlsAvailable = True
except:
	isXlsAvailable = False

try:
	import odf.text 
	import odf.table
	import odf.opendocument
	isOdsAvailable = True
except:
	isOdsAvailable = False


from ImportExportCommon import *

def executeImport(datas, model, fields):
	res = Rpc.session.execute('/object', 'execute', model, 'import_data', fields, datas, 'init', '', False, Rpc.session.context)
	if res[0]>=0:
		QMessageBox.information( None, _('Information'), _('Imported %d objects !') % (res[0]))
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
		return False
	return True

def importCsv(csv_data, fields, model):
	fname = csv_data['fname']
	try:
		content = file(fname,'rb').read()
	except Exception, e:
		QMessageBox.information( None, _('Error'), _('Error opening file: %s') % unicode(e.args) )
		return False
	try:
		input=StringIO.StringIO(content)
		data = list(csv.reader(input, quotechar=csv_data['del'], delimiter=csv_data['sep']))[int(csv_data['skip']):]
		
		datas = []
		for line in data:
			datas.append(map(lambda x:x.decode(csv_data['encoding']).encode('utf-8'), line))
	except Exception, e:
		QMessageBox.information( None, _('Error'), _('Error reading file: %s') % unicode(e.args) )
		return False

	return executeImport(datas, model, fields)

(ImportDialogUi, ImportDialogBase) = loadUiType( Common.uiPath('win_import.ui') )

class ImportDialog(QDialog, ImportDialogUi):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		ImportDialogUi.__init__(self)
		self.setupUi( self )

		self.model = None
		self.fields = None

		self.uiFileFormat.addItem( _('CSV'), 'csv' )
		if isXlsAvailable:
			self.uiFileFormat.addItem( _('Excel (XLS)'), 'xls' )
		if isOdsAvailable:
			self.uiFileFormat.addItem( _('Open Document (ODS)'), 'ods' )
		self.uiFileFormat.setCurrentIndex( 0 )
		self.updateFileFormat()

		self.connect( self.pushImport, SIGNAL('clicked()'), self.import_ )
		self.connect( self.pushClose, SIGNAL('clicked()'), self.reject )
		self.connect( self.pushAdd, SIGNAL('clicked()'), self.slotAdd )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.slotRemove )
		self.connect( self.pushRemoveAll, SIGNAL('clicked()'), self.slotRemoveAll )
		self.connect( self.pushAutoDetect, SIGNAL('clicked()'), self.slotAutoDetect )
		self.connect( self.pushOpenFile, SIGNAL('clicked()'), self.slotOpenFile )
		self.connect( self.uiFileFormat, SIGNAL('currentIndexChanged(int)'), self.updateFileFormat )

	def fileFormat(self):
		index = self.uiFileFormat.currentIndex()
		return unicode( self.uiFileFormat.itemData( index ).toString() )

	def updateFileFormat(self):
		if self.fileFormat() == 'csv':
			self.uiCsvContainer.show()
			self.uiSpreadSheetContainer.hide()
		elif self.fileFormat() == 'xls':
			self.uiCsvContainer.hide()
			self.uiSpreadSheetContainer.show()
			self.updateXlsFields()
		else:
			self.uiCsvContainer.hide()
			self.uiSpreadSheetContainer.show()
			self.updateOdsFields()

	def updateXlsFields(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Sheet List Error'), 'You must select an import file first !')
			return 
		self.uiSpreadSheetSheet.clear()
		for sheet in self.xlsSheets(fileName):
			self.uiSpreadSheetSheet.addItem( sheet, 0 )
		self.uiSpreadSheetSheet.setCurrentIndex( 0 )

	def updateOdsFields(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Sheet List Error'), 'You must select an import file first !')
			return 
		self.uiSpreadSheetSheet.clear()
		for sheet in self.odsSheets(fileName):
			self.uiSpreadSheetSheet.addItem( sheet, 0 )
		self.uiSpreadSheetSheet.setCurrentIndex( 0 )

	def setModel(self, model):
		self.model = model

	def setup( self, viewTypes, viewIds ):
		self.viewTypes = viewTypes
		self.viewIds = viewIds
		QTimer.singleShot( 0, self.initGui )

	def initGui(self):
		QApplication.setOverrideCursor( Qt.WaitCursor )
		# Pick up information of all available fields in all current views.
		try:
			self.fields = {}
			queue = ViewQueue()
			queue.setup( self.viewTypes, self.viewIds )
			while not queue.isEmpty():
				id, type = queue.next()
				view = Rpc.session.execute('/object', 'execute', self.model, 'fields_view_get', id, type, Rpc.session.context)
				self.fields.update( view['fields'] )
		except Rpc.RpcException, e:
			QApplication.restoreOverrideCursor()
			return

		self.fieldsInfo = {}
		self.fieldsInvertedInfo = {}
		self.allModel = FieldsModel()
		self.allModel.load( self.fields, self.fieldsInfo, self.fieldsInvertedInfo )
		self.uiAllFields.setModel( self.allModel )
		self.uiAllFields.sortByColumn( 0, Qt.AscendingOrder )

		self.selectedModel = FieldsModel()
		self.uiSelectedFields.setModel( self.selectedModel )
		QApplication.restoreOverrideCursor()

	def slotOpenFile(self):
		fileName = QFileDialog.getOpenFileName(self, _('File to import'))
		if fileName.isNull():
			return
		self.uiFileName.setText( fileName )
		index = self.uiFileFormat.currentIndex()
		fileName = unicode( fileName )
		if fileName.lower().endswith('.csv'):
			index = self.uiFileFormat.findData( 'csv' )
		if isXlsAvailable:
			if fileName.lower().endswith('.xls'):
				index = self.uiFileFormat.findData( 'xls' )
		if isOdsAvailable:
			if fileName.lower().endswith('.ods'):
				index = self.uiFileFormat.findData( 'ods' )
		self.uiFileFormat.setCurrentIndex( index )
		self.updateFileFormat()

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

	def csvAutoDetect(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Auto-detect error'), 'You must select an import file first !')
			return 
		separator = unicode(self.uiFieldSeparator.text()).encode('ascii','ignore').strip()
		delimiter = unicode(self.uiTextDelimiter.text()).encode('ascii','ignore').strip()
		encoding = unicode(self.uiEncoding.currentText()) or 'UTF-8'

		self.uiLinesToSkip.setValue(1)
		if len(separator) != 1:
			QMessageBox.warning(self, _('Auto-detect error'), _('Separator must be a single character.'))
			return
		if len(delimiter) != 1:
			QMessageBox.warning(self, _('Auto-detect error'), _('Delimiter must be a single character.'))
			return
		
		try:
			records = csv.reader(file(fileName), quotechar=delimiter, delimiter=separator)
		except:
			QMessageBox.warning(self, _('Auto-detect error'), _('Error opening .CSV file: Input Error.') )
			return 
		self.slotRemoveAll()
		try:
			for record in records:
				for field in record:
					if encoding:
						field = unicode(field, encoding, errors='replace') 
					self.selectedModel.addField( field, self.fieldsInvertedInfo[field] )
				break
			if self.uiLinesToSkip.value() == 0:
				self.uiLinesToSkip.setValue( 1 )
		except:
			QMessageBox.warning(self, _('Auto-detect error'), _('Error processing your first line of the file.\nField %s is unknown !') % (field) )

	def odsRecords(self, fileName, sheet):
		try:
			doc = odf.opendocument.load(fileName)
		except Exception, e:
			QMessageBox.information( None, _('Error'), _('Error reading file: %s') % unicode(e.args) )
			return []

		key = ('urn:oasis:names:tc:opendocument:xmlns:table:1.0', u'name')
		for x in doc.getElementsByType(odf.table.Table):
			if key in x.attributes and x.attributes[key] == sheet:
				#d = doc.spreadsheet
				rows = x.getElementsByType(odf.table.TableRow)
				records = []
				for row in rows:
					cells = row.getElementsByType(odf.table.TableCell)
					record = []
					for cell in cells:
						tps = cell.getElementsByType(odf.text.P)
						for x in tps:
							record.append( unicode( x.firstChild ) )
					if record:
						records.append( record )
				break
		return records

	def odsSheets(self, fileName):
		try:
			doc = odf.opendocument.load(fileName)
		except Exception, e:
			QMessageBox.information( None, _('Error'), _('Error reading file: %s') % unicode(e.args) )
			return []
		key = ('urn:oasis:names:tc:opendocument:xmlns:table:1.0', u'name')
		sheets = []
		for x in doc.getElementsByType(odf.table.Table):
			if key in x.attributes:
				sheets.append( x.attributes[key] )
		return sheets

	def xlsRecords(self, fileName, sheet):
		try:
			book = xlrd.open_workbook( fileName )
		except Exception, e:
			QMessageBox.information( None, _('Error'), _('Error reading file: %s') % unicode(e.args) )
			return []
		sheet = book.sheet_by_name(sheet)
		if sheet.nrows == 0:
			return []
		header = sheet.row_values(0)
		records = []
		for row in xrange(sheet.nrows):
			record = []
			for column in sheet.row_values(row):
				record.append( column )
			records.append( record )
		return records

	def xlsSheets(self, fileName):
		try:
			book = xlrd.open_workbook( fileName )
		except Exception, e:
			QMessageBox.information( None, _('Error'), _('Error reading file: %s') % unicode(e.args) )
			return []
		sheets = []
		for i in xrange(book.nsheets):
			sheets.append( book.sheet_by_index( i ).name )
		return sheets

	def xlsAutoDetect(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Auto-detect error'), 'You must select an import file first !')
			return 
		sheet = unicode( self.uiSpreadSheetSheet.currentText() )
		records = self.xlsRecords( fileName, sheet )
		if records:
			record = records[0]
			for field in record:
				if not field in self.fieldsInvertedInfo:
					QMessageBox.warning(self, _('Auto-detect error'), _('Error processing your first line of the file.\nField %s is unknown !') % (field) )
					return
				self.selectedModel.addField( field, self.fieldsInvertedInfo[field] )
			if self.uiSpreadSheetLinesToSkip.value() == 0:
				self.uiSpreadSheetLinesToSkip.setValue( 1 )

	def odsAutoDetect(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Auto-detect error'), 'You must select an import file first !')
			return 
		sheet = unicode( self.uiSpreadSheetSheet.currentText() )
		records = self.odsRecords( fileName, sheet )
		if records:
			record = records[0]
			for field in record:
				if not field in self.fieldsInvertedInfo:
					QMessageBox.warning(self, _('Auto-detect error'), _('Error processing your first line of the file.\nField %s is unknown !') % (field) )
					return
				self.selectedModel.addField( field, self.fieldsInvertedInfo[field] )
			if self.uiSpreadSheetLinesToSkip.value() == 0:
				self.uiSpreadSheetLinesToSkip.setValue( 1 )

	def slotAutoDetect(self):
		self.slotRemoveAll()
		if self.fileFormat() == 'csv':
			self.csvAutoDetect()
		elif self.fileFormat() == 'xls':
			self.xlsAutoDetect()
		else:
			self.odsAutoDetect()

	def importCsv(self):
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
			if not importCsv(csv, fieldsData, self.model):
				return
		self.accept()

	def importXls(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Import Error'), 'You must select an import file first !')
			return 
		sheet = unicode( self.uiSpreadSheetSheet.currentText() )

		linesToSkip = self.uiSpreadSheetLinesToSkip.value()

		fieldsData = []
		for x in range(0, self.selectedModel.rowCount() ):
			fieldsData.append( unicode( self.selectedModel.item( x ).data().toString() ) )

		records = self.xlsRecords( fileName, sheet )
		records = records[linesToSkip:]
		executeImport( records, self.model, fieldsData )
		return records

	def importOds(self):
		fileName = unicode(self.uiFileName.text())
		if not fileName:
			QMessageBox.information(self, _('Import Error'), 'You must select an import file first !')
			return 
		sheet = unicode( self.uiSpreadSheetSheet.currentText() )

		linesToSkip = self.uiSpreadSheetLinesToSkip.value()

		fieldsData = []
		for x in range(0, self.selectedModel.rowCount() ):
			fieldsData.append( unicode( self.selectedModel.item( x ).data().toString() ) )

		records = self.odsRecords( fileName, sheet )
		records = records[linesToSkip:]
		executeImport( records, self.model, fieldsData )
		return records

	def import_(self):
		if self.fileFormat() == 'csv':
			self.importCsv()
		elif self.fileFormat() == 'xls':
			self.importXls()
		else:
			self.importOds()

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
