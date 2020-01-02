# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PetroProfileDialog
                                 A QGIS plugin
 Constructs a graphical representation of drilling profiles
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-12-23
        git sha              : $Format:%H$
        copyright            : (C) 2019 by T-Systems on site service GmbH
        email                : gerrit.bette@t-systems.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

from .profileBuilder import ProfileBuilder
from .profilePainter import ProfilePainter

# This loads your .ui file so that PyQt can populate your plugin
# with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'petroProfile_dialog_base.ui'))


class PetroProfileDialog(QtWidgets.QDialog, FORM_CLASS):
    """Dialog to show the petrographic drilling profiles"""

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(PetroProfileDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.scene = QtWidgets.QGraphicsScene()
        self.drawProfiles()
        view = self.findChild(QtWidgets.QGraphicsView, "graphicsView")
        view.setScene(self.scene)

    def drawProfiles(self):
        builder = ProfileBuilder(self.showMessage)
        pac = builder.getProfilesAndConnectors(self.iface.activeLayer().selectedFeatures())
        painter = ProfilePainter(self.scene)
        painter.paint(pac)

    def showMessage(self, title, message, level):
        self.iface.messageBar().pushMessage(title, message, level)
