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
from Koo.Common import Numeric
from Koo.Common import OpenOffice
from Koo.Screen.ViewQueue import *

from Koo import Rpc

import types
import os
import codecs

from ImportExportCommon import *

def exportHtml(fname, fields, result, writeTitle):
	QApplication.setOverrideCursor( Qt.WaitCursor )
	try:
		f = codecs.open( fname, 'wb+', 'utf8' )
		f.write( '<html>' )
		f.write( '<head><title>' + _('OpenERP exported information') + '</title></head>' )
		f.write( '<table>' )
		if writeTitle:
			f.write( '<tr>' )
			for x in fields:
				x = unicode(x)
				f.write('<th>%s</th>' % x)
			f.write( '</tr>' )
		for x in result:
			row = []
			for y in x:
				y = unicode(y)
				y = y.replace('\n','<br/>').replace('\t','&nbsp;')
				y = y.replace('<','&lt;').replace('>','&gt;').replace('&','&amp;')
				row.append(y)
			f.write( '<tr>' )
			f.write( '<td>%s</td>' % ( '</td><td>'.join( row ) ) )
			f.write( '</tr>' )
		f.close()
		QApplication.restoreOverrideCursor()
		QMessageBox.information( None, _('Information'), _('%s record(s) saved!') % (str(len(result))) )
	except IOError, (errno, strerror):
		QApplication.restoreOverrideCursor()
		QMessageBox.warning( None, _('Error'), _("Operation failed !\nI/O error (%s)") % (errno))

def exportCsv(fname, fields, result, writeTitle):
	QApplication.setOverrideCursor( Qt.WaitCursor )
	try:
		fp = codecs.open( fname, 'wb+', 'utf8' )
		if writeTitle:
			fp.write( ','.join( fields ) + '\n' )
		for data in result:
			row = []
			for d in data:
				if type(d)==types.StringType:
					row.append('"' + d.replace('\n',' ').replace('\t',' ').replace('"',"\\\"") + '"')
				elif not isinstance( d, unicode ):
					row.append( unicode( d ) )
				else:
					row.append( d )
			fp.write( ','.join( row ) + '\n' )
		fp.close()
		QApplication.restoreOverrideCursor()
		QMessageBox.information( None, _('Data Export'), _('%s record(s) saved!') % (str(len(result))) )
	except IOError, (errno, strerror):
		QApplication.restoreOverrideCursor()
		QMessageBox.warning( None, _('Data Export'), _("Operation failed !\nI/O error (%s)") % (errno))
	except Exception, e:
		QApplication.restoreOverrideCursor()
		QMessageBox.warning( None, _('Data Export'), _("Error exporting data:\n%s") % unicode(e.args) )

## @brief Converts the given list of lists (data) into the appropiate type so Excel and OpenOffice.org
# set the appropiate cell format.
def convertTypes(data, fieldsType):
	for a in data:
		for b in range(len(a)):
			if type(a[b]) == type(''):
				a[b]=a[b].decode('utf-8','replace')
			elif type(a[b]) == type([]):
				if len(a[b])==2:
					a[b] = a[b][1].decode('utf-8','replace')
				else:
					a[b] = ''
			if fieldsType[b] in ('float', 'integer'):
				if Numeric.isNumeric( a[b] ):
					a[b] = float( a[b] )
	return data

def openExcel(fields, fieldsType, result, writeTitle):
	QApplication.setOverrideCursor( Qt.WaitCursor )
	try:
		from win32com.client import Dispatch
		application = Dispatch("Excel.Application")
		application.Workbooks.Add()

		sheet = application.ActiveSheet
		row = 1
		if writeTitle:
			for col in range(len(fields)):
				sheet.Cells( row, col + 1 ).Value = fields[col]
			row += 1

		result = convertTypes( result, fieldsType )
		sheet.Range(sheet.Cells(row, 1), sheet.Cells(row + len(result)-1, len(fields))).Value = result
		
		application.Visible = 1
		QApplication.restoreOverrideCursor()
	except Exception, e:
		QApplication.restoreOverrideCursor()
		QMessageBox.warning(None, _('Error'), _('Error opening Excel:\n%s') % unicode(e.args) )

# Based on code by Dukai Gabor posted in openobject-client bugs:
# https://bugs.launchpad.net/openobject-client/+bug/399278 
def openOpenOffice(fields, fieldsType, result, writeTitle):
	QApplication.setOverrideCursor( Qt.WaitCursor )
	try:
		import time

		OpenOffice.OpenOffice.start()

		for i in range(30):
			ooo = OpenOffice.OpenOffice()
			if ooo and ooo.desktop:
				break
			time.sleep(1)
		doc = ooo.desktop.loadComponentFromURL("private:factory/scalc",'_blank',0,())
		sheet = doc.CurrentController.ActiveSheet

		row = 0
		if writeTitle:
			for col in xrange(len(fields)):
				cell = sheet.getCellByPosition(col, row)
				cell.String = fields[col]
			row += 1

		result = convertTypes( result, fieldsType )
		result = tuple( [tuple(x) for x in result] )

		cellrange = sheet.getCellRangeByPosition(0, row, len(fields) - 1, row + len(result) - 1)
		cellrange.setDataArray(result)
		QApplication.restoreOverrideCursor()
	except Exception, e:
		QApplication.restoreOverrideCursor()
		QMessageBox.warning(None, _('Error'), _('Error Opening OpenOffice.org:\n%s') % unicode(e.args) )

def exportData(ids, model, fields, prefix=''):
	data = Rpc.session.execute('/object', 'execute', model, 'export_data', ids, fields, Rpc.session.context)
	# After 5.0 data is returned directly (no 'datas' key in a dictionary).
	if isinstance(data, dict) and 'datas' in data:
		data = data['datas']
	return data

(ExportDialogUi, ExportDialogBase) = loadUiType( Common.uiPath('win_export.ui') )

class ExportDialog( QDialog, ExportDialogUi ):
	exports = {}

	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		ExportDialogUi.__init__(self)
		self.setupUi( self )

		self.ids = []
		self.model = None
		self.fields = None
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.export )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		self.connect( self.pushAdd, SIGNAL('clicked()'), self.add )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.remove )
		self.connect( self.pushRemoveAll, SIGNAL('clicked()'), self.removeAll )
		self.connect( self.pushSave, SIGNAL('clicked()'), self.save )
		self.connect( self.pushRemoveExport, SIGNAL('clicked()'), self.removeExport )
		self.connect( self.uiPredefined, SIGNAL('activated(const QModelIndex&)'), self.loadCurrentStored )

	def setModel( self, model ):
		self.model = model

	def setIds( self, ids ):
		self.ids = ids

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

		for key, export in ExportDialog.exports.iteritems():
			self.uiFormat.addItem( export['label'], QVariant( key ) )	

		self.fieldsInfo = {}
		self.allModel = FieldsModel()
		self.allModel.load( self.fields, self.fieldsInfo )
		self.uiAllFields.setModel( self.allModel )
		self.uiAllFields.sortByColumn( 0, Qt.AscendingOrder )

		self.selectedModel = FieldsModel()
		self.uiSelectedFields.setModel( self.selectedModel )

		self.storedModel = StoredExportsModel()
		self.storedModel.load( self.model, self.fieldsInfo )
		self.uiPredefined.setModel( self.storedModel )
		self.uiPredefined.hideColumn(0)
		self.uiPredefined.hideColumn(1)

		QApplication.restoreOverrideCursor()

	@staticmethod
	def registerExport(key, label, requiresFileName, function):
		ExportDialog.exports[ key ] = {
			'label': label,
			'requiresFileName': requiresFileName,
			'function': function
		}

	@staticmethod
	def unregisterExport(key):
		del ExportDialog.exports[ key ]

	def removeExport(self):
		idx = self.uiPredefined.selectionModel().selectedRows(1)
		if len(idx) != 1:
			return
		idx = idx[0]
		id = int( unicode( self.storedModel.itemFromIndex( idx ).text() ) )
		ir_export = Rpc.RpcProxy('ir.exports')
		ir_export.unlink([id])
		self.storedModel.load( self.model, self.fieldsInfo )

	def loadCurrentStored(self):
		idx = self.uiPredefined.selectionModel().selectedRows(0)
		if len(idx) != 1:
			return
		idx = idx[0]
		fields = unicode( self.storedModel.itemFromIndex( idx ).text() )
		fields = fields.split(', ') 
		if self.selectedModel.rowCount() > 0:
			self.selectedModel.removeRows(0, self.selectedModel.rowCount() )
		for x in fields:
			newItem = QStandardItem()
			newItem.setText( unicode( self.fieldsInfo[x]['string'] ) )
			newItem.setData( QVariant(x) )
			self.selectedModel.appendRow( newItem )

	def export(self):
		fields = []
		fieldTitles = []
		for x in range(0, self.selectedModel.rowCount() ):
			fields.append( unicode( self.selectedModel.item( x ).data().toString() ) )
			fieldTitles.append( unicode( self.selectedModel.item( x ).text() ) )
		action = unicode( self.uiFormat.itemData(self.uiFormat.currentIndex()).toString() )
		result = exportData(self.ids, self.model, fields)
		export = ExportDialog.exports[action]
		if export['requiresFileName']:
			fileName = QFileDialog.getSaveFileName( self, _('Export Data') )
			export['function'](fileName, fieldTitles, result, self.uiAddFieldNames.isChecked() )
		else:
			fieldsType = [self.fieldsInfo[x]['type'] for x in fields]
			export['function'](fieldTitles, fieldsType, result, self.uiAddFieldNames.isChecked() )

	def add(self):
		idx = self.uiAllFields.selectionModel().selectedRows()
		if len(idx) != 1:
			return 
		idx = idx[0]
		item = self.allModel.itemFromIndex( idx )
		newItem = QStandardItem( item )
		newItem.setText( self.fullPathText(item) )
		newItem.setData( QVariant(self.fullPathData(item)) )
		self.selectedModel.appendRow( newItem )

	def remove(self):
		idx = self.uiSelectedFields.selectedIndexes()
		if len(idx) != 1:
			return
		idx = idx[0]
		self.selectedModel.removeRows( idx.row(), 1 )

	def removeAll(self):
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

	def save(self):
		name, ok = QInputDialog.getText(self, '', _('What is the name of this export?'))
		if not ok:
			return
		ir_export = Rpc.RpcProxy('ir.exports')
		fields = []
		for x in range(0, self.selectedModel.rowCount() ):
			fields.append( unicode( self.selectedModel.item(x).data().toString() ) )

		ir_export.create({
			'name' : unicode(name), 
			'resource' : self.model,
			'export_fields' : [(0, 0, {'name' : f}) for f in fields]
		})
		self.storedModel.load( self.model, self.fieldsInfo )


# Add OpenOffice.org export only if it's available.
if OpenOffice.isOpenOfficeAvailable:
	ExportDialog.registerExport('openoffice', _('Open with OpenOffice.org'), False, openOpenOffice)
# Add Excel export only if it's available
if os.name == 'nt':
	try:
		from win32com.client import Dispatch
		application = Dispatch("Excel.Application")
		ExportDialog.registerExport('excel', _('Open with Excel'), False, openExcel)
	except:
		pass
ExportDialog.registerExport('csv', _('Save as CSV'), True, exportCsv)
ExportDialog.registerExport('html', _('Save as HTML'), True, exportHtml)

# This model holds the information of the predefined exports
# For each item we store the fields list (with the internal name), the name of the export and
# the fields list (with the external -user friendly- name).
class StoredExportsModel( QStandardItemModel ):
	def __init__(self):
		QStandardItemModel.__init__(self)
		self.rootItem = self.invisibleRootItem()
		self.setColumnCount( 4 )
		self.setHeaderData( 0, Qt.Horizontal, QVariant('Field list (internal names)') )
		self.setHeaderData( 1, Qt.Horizontal, QVariant('Export id') )
		self.setHeaderData( 2, Qt.Horizontal, QVariant( _('Export name') ) )
		self.setHeaderData( 3, Qt.Horizontal, QVariant( _('Exported fields') ) )

	def load(self, model, fieldsInfo):
		if self.rowCount() > 0:
			self.removeRows(0, self.rowCount())
		ir_export = Rpc.RpcProxy('ir.exports')
		ir_export_line = Rpc.RpcProxy('ir.exports.line')
		export_ids = ir_export.search([('resource', '=', model)])
		for export in ir_export.read(export_ids):
			fields = ir_export_line.read(export['export_fields'])

			allFound = True
			for f in fields:
				if not f['name'] in fieldsInfo:
					allFound = False
					break
			if not allFound:
				continue

			items = [ QStandardItem( ', '.join([f['name'] for f in fields]) ), QStandardItem( str(export['id']) ), QStandardItem( export['name'] ), QStandardItem( ', '.join( [fieldsInfo[f['name']]['string'] for f in fields] ) ) ]
			self.rootItem.appendRow( items )
