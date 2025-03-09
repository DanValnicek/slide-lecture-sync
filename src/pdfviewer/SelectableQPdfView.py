from PySide6.QtCore import Signal, Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtPdf import QPdfSelection
from PySide6.QtPdfWidgets import QPdfView


class SelectableQPdfView(QPdfView):
    selectionChanged = Signal(int, QPointF, QPointF)

    _start_selection: QPointF | None = None
    _end_selection: QPointF | None = None

    def point_move_margins(self, point: QPointF):
        # leftMargin = self.documentMargins().toMarginsF().left()
        leftMargin = self.viewportMargins().toMarginsF().left()
        # topMargin = self.documentMargins().toMarginsF().top()
        topMargin = self.viewportMargins().toMarginsF().top()
        return QPointF(point.x() - leftMargin, point.y() - topMargin)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._start_selection = self.point_move_margins(event.position())

    def mouseMoveEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._start_selection:
            # x1, y1 = self._start_selection.toTuple()
            # x2, y2 = event.position().toTuple()
            bounding_box = QRectF(self._start_selection, self.point_move_margins(event.position()))
            self._end_selection = bounding_box.bottomRight()
            print(bounding_box)
            print(bounding_box.normalized())
            print(self._start_selection)
            print(event.position())
            self.selectionChanged.emit(
                self.pageNavigator().currentPage(),
                bounding_box.topLeft(),
                bounding_box.bottomRight()
            )

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._start_selection = self._end_selection = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_rects = []  # Stores selection rectangles (in page coordinates)

    def set_selection(self, selection: QPdfSelection):
        """Update selection rectangles and refresh view."""
        if not selection.isValid():
            self.selected_rects = []
        else:
            self.selected_rects = selection.bounds()

        self.viewport().update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw selection highlights dynamically."""
        super().paintEvent(event)  # First, render the PDF
        if not self.selected_rects or not self.document():
            return  # No selection or document is not set

        # Get the current page size
        page_index = self.pageNavigator().currentPage()
        page_size = self.document().pagePointSize(page_index)  # QSizeF

        if page_size.isEmpty():
            return  # Invalid page size
        painter = QPainter(self.viewport())
        painter.setBrush(QColor(0, 100, 255, 100))  # Semi-transparent blue
        painter.setPen(Qt.NoPen)
        painter.setBrushOrigin(self.viewportMargins().left() + self.documentMargins().left(),
                               self.viewportMargins().top() + self.documentMargins().top())
        # painter.setBrushOrigin(self.documentMargins().left(), self.documentMargins().top())
        view_size = self.viewport()
        height = view_size.height() - self.viewportMargins().top() - self.viewportMargins().bottom() - self.documentMargins().bottom() - self.documentMargins().top()
        width = view_size.width() - self.viewportMargins().left() - self.viewportMargins().right() - self.documentMargins().left() - self.documentMargins().right()

        painter.scale(width / page_size.width(), height / page_size.height())

        for page_rect in self.selected_rects:
            # view_rect = self.pdf_to_view(page_rect, page_size)
            print(page_rect)
            painter.drawPolygon(page_rect)

        painter.end()

    def pdf_to_view(self, pdf_polygon: QRectF, page_size):
        """Convert PDF page coordinates to QPdfView widget coordinates."""
        if not self.viewport():
            return QRectF()  # Avoid errors

        view_width = self.viewport().width()
        view_height = self.viewport().height()

        # Scale PDF rectangle to viewport size
        scale_x = view_width / page_size.width()
        scale_y = view_height / page_size.height()
        pdf_rect = pdf_polygon.boundingRect()

        return QRectF(
            pdf_rect.x() * scale_x,
            pdf_rect.y() * scale_y,
            pdf_rect.width() * scale_x,
            pdf_rect.height() * scale_y,
        )

    def resizeEvent(self, event):
        """Redraw selection highlights when the window is resized."""
        super().resizeEvent(event)
        self.viewport().update()

    def scrollContentsBy(self, dx, dy):
        """Redraw selection highlights when scrolling occurs."""
        super().scrollContentsBy(dx, dy)
        self.viewport().update()
