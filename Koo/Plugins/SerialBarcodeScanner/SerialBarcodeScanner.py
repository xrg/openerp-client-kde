##############################################################################
#
# Copyright (c) 2009 Albert Cervera i Areny <albert@nan-tic.com>
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

try:
	import serial
	isSerialAvailable = True
except:
	isSerialAvailable = False
	Debug.info('PySerial not found. Serial Barcode Scanners will not be available.')

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from Common import Debug

## @brief This class reads from a Barcode Scanner connected to the serial port and sends
# its input as key events to the application.
class SerialBarcodeScanner(QThread):
	def __init__(self, parent=None):
		QThread.__init__(self, parent)

	def run(self):
		device = serial.Serial(0)
		while True:
			data = device.read()
			if data:
				char = data[0]
				try:
					key = eval('Qt.Key_%s' % char)
				except:
					Debug.warning('Could not find key for char "%s".' % char )
					pass
				event = QKeyEvent( QEvent.KeyPress, key, QApplication.keyboardModifiers(), char )
				QApplication.postEvent( QApplication.focusWidget(), event )
				event = QKeyEvent( QEvent.KeyRelease, key, QApplication.keyboardModifiers(), char )
				QApplication.postEvent( QApplication.focusWidget(), event )
