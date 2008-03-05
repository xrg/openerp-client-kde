#!/usr/bin/python

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
from mainwindow import *

app = QApplication( sys.argv )
window = MainWindow()
window.show()
app.exec_()
