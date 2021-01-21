# -*- coding: utf-8 -*-
"""
    geoCore - a QGIS plugin for drawing drilling profiles
    Copyright (C) 2019 - 2021  Gerrit Bette, T-Systems on site services GmbH

    This file is part of geoCore.

    geoCore is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    geoCore is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with geoCore.  If not, see <https://www.gnu.org/licenses/>.

/****************************************************************************************
 Scaffolding generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-12-23
        git sha              : $Format:%H$
 ****************************************************************************************/
"""
import os
from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QAction, QActionGroup, QMenu, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QPainter, QImage, QColor
from qgis.PyQt.QtSvg import QSvgGenerator
from qgis.PyQt.QtCore import QRectF, QEvent
from qgis.core import Qgis, QgsMessageLog

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
        self._setupScene()
        self._setupGeoDirectionActions()

    def _setupScene(self):
        """Setup a new scene"""
        self.scene = QtWidgets.QGraphicsScene()
        self.view = self.findChild(QtWidgets.QGraphicsView, "graphicsView")
        self.view.setScene(self.scene)
        self.view.viewport().installEventFilter(self)

    def _setupGeoDirectionActions(self):
        self._nsAction = QAction("North -> South", self)
        self._nsAction.triggered.connect(self.drawProfilesNorthSouth)
        self._nsAction.setEnabled(True)
        self._nsAction.setCheckable(True)

        self._snAction = QAction("South -> North", self)
        self._snAction.triggered.connect(self.drawProfilesSouthNorth)
        self._snAction.setEnabled(True)
        self._snAction.setCheckable(True)

        self._weAction = QAction("West -> East", self)
        self._weAction.triggered.connect(self.drawProfilesWestEast)
        self._weAction.setEnabled(True)
        self._weAction.setCheckable(True)

        self._ewAction = QAction("East -> West", self)
        self._ewAction.triggered.connect(self.drawProfilesEastWest)
        self._ewAction.setEnabled(True)
        self._ewAction.setCheckable(True)

    def _getActions(self):
        """Get actions that are displayed in the context menu"""
        actions = []

        exportAction = QAction("Export as...", self)
        exportAction.triggered.connect(self._exportToFile)
        exportAction.setEnabled(True)
        actions.append(exportAction)

        sep = QAction("", self)
        sep.setSeparator(True)
        actions.append(sep)

        group = QActionGroup(self)
        
        group.addAction(self._nsAction)
        actions.append(self._nsAction)
        
        group.addAction(self._snAction)
        actions.append(self._snAction)

        group.addAction(self._weAction)
        actions.append(self._weAction)

        group.addAction(self._ewAction)
        actions.append(self._ewAction)

        sepAbout = QAction("", self)
        sepAbout.setSeparator(True)
        actions.append(sepAbout)

        manualAction = QAction("Manual...", self)
        manualAction.triggered.connect(self._openManual)
        manualAction.setEnabled(True)
        actions.append(manualAction)

        aboutAction = QAction("About...", self)
        aboutAction.triggered.connect(self._aboutPlugin)
        aboutAction.setEnabled(True)
        actions.append(aboutAction)        

        return actions

    def contextMenuEvent(self, e):
        """Show context menu"""
        m = QMenu()
        for a in self._getActions():
            m.addAction(a)
        m.exec(e.globalPos())
        e.setAccepted(True)

    def showEvent(self, e):
        """Override showEvent"""
        super().showEvent(e)
        self.drawProfilesNorthSouth()

    def wheelEvent(self, e):
        """Zoom in/out"""
        delta = e.angleDelta()
        if delta.isNull():
            return        
        s =  1.0
        if delta.y() > 0:
            s = 1.15
        else:
            s = 0.85 
        self.view.scale(s, s)

    def eventFilter(self, obj, e):        
        if e.type() == QEvent.Wheel:
            return True
        else:
            return super().eventFilter(obj, e)

    def _exportToFile(self):
        """Export drawing to file"""
        name = self._getFilename()
        if (name is None) or (len(name) == 0):
            return
        
        if Path(name).suffix.upper() == ".SVG":
            self._exportWithPainter(name, self._svgPaintDevice)
        else:
            self._exportWithPainter(name, self._imgPaintDevice)

    def _svgPaintDevice(self, name, sourceRect, targetRect):
        """Get QSvgGenerator as paint device"""
        generator = QSvgGenerator()
        generator.setDescription("This SVG was generated with the geoCore plugin of QGIS, written by T-Systems on site services GmbH")
        generator.setTitle("geoCore")
        generator.setSize(sourceRect.size().toSize())
        generator.setViewBox(targetRect)
        generator.setFileName(name)
        return generator

    def _imgPaintDevice(self, name, sourceRect, targetRect):
        """Get QImage as paint device"""
        img = QImage(sourceRect.width(), sourceRect.height(), QImage.Format_ARGB32)
        img.fill(QColor("transparent"))
        return img

    def _exportWithPainter(self, name, getPaintDevice):
        """Export as image file"""
        try:
            self.scene.clearSelection()
            margin = 5
            sourceRect = self.scene.itemsBoundingRect()
            sourceRect.adjust(-margin, -margin, margin, margin)

            targetRect = QRectF(0, 0, sourceRect.width(), sourceRect.height())

            pd = getPaintDevice(name, sourceRect, targetRect)

            painter = QPainter()
            painter.begin(pd)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter, targetRect, sourceRect)
            painter.end()
            if hasattr(pd, 'save') and callable(pd.save):
                pd.save(name)
            QgsMessageLog.logMessage("exported to {}".format(name), level=Qgis.Info)
        except:
            self.showMessage("Error", "Failed to export to {}".format(name), Qgis.Critical)

    def _getFilename(self):
        """Get file name via file dialog"""
        home = str(Path.home())
        name = QFileDialog.getSaveFileName(self, "Export to file", home, "Vector graphics (*.svg);;Images (*.png *.jpg)")

        if (name is None) or (len(name[0]) == 0):
            return None

        filename = name[0]
        suffix = Path(filename).suffix
        if len(suffix) == 0:
            if "svg" in name[1]:
                filename = filname + ".svg"
            else:
                filename = filname + ".png"

        return filename

    def drawProfilesNorthSouth(self):
        self._nsAction.setChecked(True)
        crit = lambda f: -f.attribute('ycoord') # north -> south
        self._drawProfiles(crit)

    def drawProfilesSouthNorth(self):
        self._snAction.setChecked(True)
        crit = lambda f: f.attribute('ycoord') # south -> north
        self._drawProfiles(crit)

    def drawProfilesWestEast(self):
        self._weAction.setChecked(True)
        crit = lambda f: f.attribute('xcoord') # west -> east
        self._drawProfiles(crit)

    def drawProfilesEastWest(self):
        self._ewAction.setChecked(True)
        crit = lambda f: -f.attribute('xcoord') # east -> west
        self._drawProfiles(crit)

    def _drawProfiles(self, sortCrit):
        """Draw the selected drilling profiles"""
        self.scene.clear()
        features = self._getSortedDrillingPositions(sortCrit)
        builder = ProfileBuilder(self.iface.activeLayer().name(), self.showMessage)
        pac = builder.getProfilesAndConnectors(features)
        painter = ProfilePainter(self.scene, self.view.height())
        painter.applyScale(1.0, None)
        painter.paint(pac, len(pac) == 1)
        self.view.resetTransform()
        self.view.setSceneRect(self.scene.itemsBoundingRect())

    def _getSortedDrillingPositions(self, crit):
        features = self.iface.activeLayer().selectedFeatures()        
        return sorted(features, key=crit)

    def _aboutPlugin(self):
        QMessageBox.about(self, "About", 
            """<h1>geoCore</h1>
            <p>
            Copyright (C) 2019-2021  Gerrit Bette, T-Systems on site services GmbH<br>
            This program comes with ABSOLUTELY NO WARRANTY. 
            This is free software, and you are welcome to redistribute it
            under certain conditions; see 
            <a href="https://www.gnu.org/licenses/gpl-3.0-standalone.html">
            https://www.gnu.org/licenses</a> for details.
            </p>
            <p>
            <a href="https://github.com/t-systems-on-site-services-gmbh/geoCore/blob/master/geoCore/help/usage.md">Manual</a>
            </p>
            <p>
            Citation: G. Bette & M. Mennenga 2020:  t-systems-on-site-services-gmbh/geoCore v0.7 (Version v0.7). Zenodo. http://doi.org/10.5281/zenodo.4347497
            </p>
            """)
            
    def _openManual(self):
        script_dir = os.path.dirname(__file__)
        rel_path = "help/usage.html"
        abs_file_path = os.path.join(script_dir, rel_path)
        os.system("start " + abs_file_path)

    def showMessage(self, title, message, level):
        """Display a message in the main window's messageBar"""
        self.iface.messageBar().pushMessage(title, message, level)
