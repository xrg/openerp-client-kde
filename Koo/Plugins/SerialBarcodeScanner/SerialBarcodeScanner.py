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


from Common import Debug
from PyQt4.QtCore import *
from PyQt4.QtGui import *


try:
	import serial
	isSerialAvailable = True
except:
	isSerialAvailable = False
	Debug.info('PySerial not found. Serial Barcode Scanners will not be available.')


## @brief This class reads from a Barcode Scanner connected to the serial port and sends
# its input as key events to the application.
class SerialBarcodeScanner(QThread):
	Keys = {
		'-': 'Minus',
		'+': 'Plus',
		'.': 'Period',
		'/': 'Slash',
		',': 'Comma',
		'*': 'Asterisk',
		'%': 'Percent',
		' ': 'Space',
	}
	def __init__(self, parent=None):
		QThread.__init__(self, parent)

	def run(self):
		try:
			device = serial.Serial(0)
		except:
			Debug.info('Could not open Serial device. Serial Barcode Scanners will not be available.')
			return

		while True:
			try:
				data = device.read()
			except:
				Debug.error('Could not read from serial device. Serial Barcode Scanner stopped.')
				return
			# In some cases (application lost focus, for example), QApplication.focusWidget()
			# may return None. In those cases we simple ignore barcode input.
			if not QApplication.focusWidget():
				continue
			if data:
				char = data[0]
				try:
					key = char.upper()
					key = SerialBarcodeScanner.Keys.get( key, key )
					key = eval('Qt.Key_%s' % key)
				except:
					Debug.warning('Could not find key for char "%s".' % char )
					continue
				# Send Key Press
				event = QKeyEvent( QEvent.KeyPress, key, QApplication.keyboardModifiers(), char )
				QApplication.postEvent( QApplication.focusWidget(), event )
				# Send Key Release
				event = QKeyEvent( QEvent.KeyRelease, key, QApplication.keyboardModifiers(), char )
				QApplication.postEvent( QApplication.focusWidget(), event )

