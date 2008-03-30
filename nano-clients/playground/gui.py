#!/usr/bin/python

from common import localization
localization.initializeTranslations()

# Load this after localization as these modules depend on it
from common import notifier, common

# Declare notifier handlers for the whole application
notifier.errorHandler = common.error
notifier.warningHandler = common.warning


from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
from mainwindow import *


app = QApplication( sys.argv )

localization.initializeQtTranslations()
window = MainWindow()
window.show()
app.exec_()
