# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import math
import sys

from PySide6.QtCore import QPoint, QStandardPaths, QUrl, Slot, Signal
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (QDialog, QFileDialog, QMainWindow, QMessageBox,
                               QSpinBox)
from PySide6.QtCore import QModelIndex, QPoint, QStandardPaths, QUrl, Slot, Qt, QEvent, Signal

from src.VideoInfo import PresentationSlideIntervals
from src.VideoPresentationProcessingWidget import VideoPresentationProcessingWidget
from zoomselector import ZoomSelector
from ui_mainwindow import Ui_MainWindow
from zoomselector import ZoomSelector

ZOOM_MULTIPLIER = math.sqrt(2.0)


class MainWindow(QMainWindow):
    document_location_changed = Signal(QUrl)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.m_zoomSelector = ZoomSelector(self)
        self.m_pageSelector = QSpinBox(self)
        self.m_document = QPdfDocument(self)
        self.m_fileDialog = None

        self.document_location = None

        self.ui.setupUi(self)

        self.m_zoomSelector.setMaximumWidth(150)
        self.ui.mainToolBar.insertWidget(self.ui.actionZoom_In, self.m_zoomSelector)

        self.ui.mainToolBar.insertWidget(self.ui.actionForward, self.m_pageSelector)
        self.m_pageSelector.valueChanged.connect(self.page_selected)
        nav = self.ui.pdfView.pageNavigator()
        nav.currentPageChanged.connect(self.m_pageSelector.setValue)
        nav.backAvailableChanged.connect(self.ui.actionBack.setEnabled)
        nav.forwardAvailableChanged.connect(self.ui.actionForward.setEnabled)

        self.m_zoomSelector.zoom_mode_changed.connect(self.ui.pdfView.setZoomMode)
        self.m_zoomSelector.zoom_factor_changed.connect(self.ui.pdfView.setZoomFactor)
        self.m_zoomSelector.reset()

        self.ui.tabWidget.setTabEnabled(1, True)  # disable 'Pages' tab for now

        self.ui.pdfView.setDocument(self.m_document)

        self.ui.pdfView.zoomFactorChanged.connect(self.m_zoomSelector.set_zoom_factor)
        self.open_video_processors = []

    @Slot(QUrl)
    def open(self, doc_location):
        if doc_location.isLocalFile():
            self.m_document.load(doc_location.toLocalFile())
            document_title = self.m_document.metaData(QPdfDocument.MetaDataField.Title)
            self.setWindowTitle(document_title if document_title else "PDF Viewer")
            self.page_selected(0)
            self.m_pageSelector.setMaximum(self.m_document.pageCount() - 1)
            self.document_location = doc_location
            self.document_location_changed.emit(doc_location)
        else:
            message = f"{doc_location} is not a valid local file"
            print(message, file=sys.stderr)
            QMessageBox.critical(self, "Failed to open", message)

    @Slot(int)
    def page_selected(self, page):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(page, QPoint(), nav.currentZoom())

    @Slot()
    def on_actionOpen_triggered(self):
        if not self.m_fileDialog:
            directory = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
            self.m_fileDialog = QFileDialog(self, "Choose a PDF", directory)
            self.m_fileDialog.setAcceptMode(QFileDialog.AcceptOpen)
            self.m_fileDialog.setMimeTypeFilters(["application/pdf"])
        if self.m_fileDialog.exec() == QDialog.Accepted:
            to_open = self.m_fileDialog.selectedUrls()[0]
            if to_open.isValid():
                self.open(to_open)

    @Slot()
    def on_actionQuit_triggered(self):
        self.close()

    @Slot()
    def on_actionAbout_triggered(self):
        QMessageBox.about(self, "About PdfViewer",
                          "An example using QPdfDocument")

    @Slot()
    def on_actionAbout_Qt_triggered(self):
        QMessageBox.aboutQt(self)

    @Slot()
    def on_actionZoom_In_triggered(self):
        factor = self.ui.pdfView.zoomFactor() * ZOOM_MULTIPLIER
        self.ui.pdfView.setZoomFactor(factor)

    @Slot()
    def on_actionZoom_Out_triggered(self):
        factor = self.ui.pdfView.zoomFactor() / ZOOM_MULTIPLIER
        self.ui.pdfView.setZoomFactor(factor)

    @Slot()
    def on_actionPrevious_Page_triggered(self):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(nav.currentPage() - 1, QPoint(), nav.currentZoom())

    @Slot()
    def on_actionNext_Page_triggered(self):
        nav = self.ui.pdfView.pageNavigator()
        nav.jump(nav.currentPage() + 1, QPoint(), nav.currentZoom())

    @Slot()
    def on_actionContinuous_triggered(self):
        cont_checked = self.ui.actionContinuous.isChecked()
        mode = QPdfView.PageMode.MultiPage if cont_checked else QPdfView.PageMode.SinglePage
        self.ui.pdfView.setPageMode(mode)

    @Slot()
    def on_actionBack_triggered(self):
        self.ui.pdfView.pageNavigator().back()

    @Slot()
    def on_actionForward_triggered(self):
        self.ui.pdfView.pageNavigator().forward()

    @Slot()
    def text_selected(self, page_num, start_pt, end_pt):
        if self.m_document.status() == QPdfDocument.Status.Ready:
            selection = self.m_document.getSelection(page_num, start_pt, end_pt)
            if selection:
                text = selection.text()
                print(text)

    def open_video_presentation_processor(self):
        widget = VideoPresentationProcessingWidget()
        widget.show()
        self.open_video_processors.append(widget)
