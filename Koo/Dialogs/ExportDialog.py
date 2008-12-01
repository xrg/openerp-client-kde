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

from Koo import Rpc
import sets

import types
import os
import codecs

from ImportExportCommon import *

def exportHtml(fname, fields, result, write_title=False):
	try:
		f = file(fname, 'wb+')
		f.write( '<html>' )
		f.write( '<head><title>' + _('OpenERP exported information') + '</title></head>' )
		f.write( '<table>' )
		if write_title:
			f.write( '<tr>' )
			for x in fields:
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
		QMessageBox.information( None, '', _('%s record(s) saved!') % (str(len(result))) )
	except IOError, (errno, strerror):
		QMessageBox.warning( None, '', _("Operation failed !\nI/O error (%s)") % (errno))

def exportCsv(fname, fields, result, write_title=False):
	try:
		fp = codecs.open( fname, 'wb+', 'utf8' )
		if write_title:
			fp.write( ','.join( fields ) + '\n' )
		for data in result:
			row = []
			for d in data:
				if type(d)==types.StringType:
					row.append('"' + d.replace('\n',' ').replace('\t',' ').replace('"',"\\\"") + '"')
				else:
					row.append(d)
			fp.write( ','.join( row ) + '\n' )
		fp.close()
		QMessageBox.information( None, _('Data Export'), _('%s record(s) saved!') % (str(len(result))) )
	except IOError, (errno, strerror):
		QMessageBox.warning( None, _('Data Export'), _("Operation failed !\nI/O error (%s)") % (errno))
	except Except:
		QMessageBox.warning( None, _('Data Export'), _("Error exporting data.") )

def openExcel(fields, result):
	try:
		from win32com.client import Dispatch
		xlApp = Dispatch("Excel.Application")
		xlApp.Workbooks.Add()
		for col in range(len(fields)):
			xlApp.ActiveSheet.Cells(1,col+1).Value = fields[col]
		sht = xlApp.ActiveSheet
		for a in result:
			for b in range(len(a)):
				if type(a[b]) == type(''):
					a[b]=a[b].decode('utf-8','replace')
				elif type(a[b]) == type([]):
					if len(a[b])==2:
						a[b] = a[b][1].decode('utf-8','replace')
					else:
						a[b] = ''
		sht.Range(sht.Cells(2, 1), sht.Cells(len(result)+1, len(fields))).Value = result
		xlApp.Visible = 1
	except:
		QMessageBox.warning(None, '', _('Error opening Excel !'))

def exportData(ids, model, fields, prefix=''):
	data = Rpc.session.execute('/object', 'execute', model, 'export_data', ids, fields)
	return data

(ExportDialogUi, ExportDialogBase) = loadUiType( Common.uiPath('win_export.ui') )

class ExportDialog( QDialog, ExportDialogUi ):
	def __init__(self, model, ids, fields, preload =[], parent=None):
		QDialog.__init__(self, parent)
		ExportDialogUi.__init__(self)
		self.setupUi( self )

		self.ids = ids
		self.model = model
		self.connect( self.pushAccept, SIGNAL('clicked()'), self.slotAccept )
		self.connect( self.pushCancel, SIGNAL('clicked()'), self.reject )
		self.connect( self.pushAdd, SIGNAL('clicked()'), self.slotAdd )
		self.connect( self.pushRemove, SIGNAL('clicked()'), self.slotRemove )
		self.connect( self.pushRemoveAll, SIGNAL('clicked()'), self.slotRemoveAll )
		self.connect( self.pushSave, SIGNAL('clicked()'), self.slotSave )
		self.connect( self.pushRemoveExport, SIGNAL('clicked()'), self.slotRemoveExport )
		self.connect( self.uiPredefined, SIGNAL('activated(const QModelIndex&)'), self.loadCurrentStored )

		if os.name == 'nt':
			self.uiFormat.addItem( _("Open with Excel"), QVariant('excel') )

		self.uiFormat.addItem( _("Save as CSV"), QVariant('csv') )
		self.uiFormat.addItem( _("Save as HTML"), QVariant('html') )

		self.fieldsInfo = {}
		self.allModel = FieldsModel()
		self.setCursor( Qt.WaitCursor )
		self.allModel.load( fields, self.fieldsInfo )
		self.setCursor( Qt.ArrowCursor )
		self.uiAllFields.setModel( self.allModel )
		self.uiAllFields.sortByColumn( 0, Qt.AscendingOrder )

		self.selectedModel = FieldsModel()
		self.uiSelectedFields.setModel( self.selectedModel )

		self.storedModel = StoredExportsModel()
		self.storedModel.load( self.model, self.fieldsInfo )
		self.uiPredefined.setModel( self.storedModel )
		self.uiPredefined.hideColumn(0)
		self.uiPredefined.hideColumn(1)

	def slotRemoveExport(self):
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

	def slotAccept(self):
		fields = []
		fields2 = []
		for x in range(0, self.selectedModel.rowCount() ):
			fields.append( unicode( self.selectedModel.item( x ).data().toString() ) )
			fields2.append( unicode( self.selectedModel.item( x ).text() ) )
		action = unicode( self.uiFormat.itemData(self.uiFormat.currentIndex()).toString() )
		result = exportData(self.ids, self.model, fields)
		if action == 'excel':
			openExcel(fields2, result)
		else:
			fname = QFileDialog.getSaveFileName( self, _('Export Data') )
			if not fname.isNull():
				if action == 'csv':
					exportCsv(fname, fields2, result, self.uiAddFieldNames.isChecked() )
				else:
					exportHtml(fname, fields2, result, self.uiAddFieldNames.isChecked() )

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

	def slotSave(self):
		name, ok = QInputDialog.getText(self, '', _('What is the name of this export?'))
		if not ok:
			return
		ir_export = Rpc.RpcProxy('ir.exports')
		fields = []
		for x in range(0, self.selectedModel.rowCount() ):
			fields.append( unicode( self.selectedModel.item(x).data().toString() ) )

		ir_export.create({'name' : unicode(name), 'resource' : self.model, 'export_fields' : [(0, 0, {'name' : f}) for f in fields]})
		self.storedModel.load( self.model, self.fieldsInfo )

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
			items = [ QStandardItem( ', '.join([f['name'] for f in fields]) ), QStandardItem( str(export['id']) ), QStandardItem( export['name'] ), QStandardItem( ', '.join( [fieldsInfo[f['name']]['string'] for f in fields] ) ) ]
			self.rootItem.appendRow( items )
			
