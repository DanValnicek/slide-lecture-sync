from datetime import time, timedelta, datetime

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QProgressBar, QWidget, QHBoxLayout, QLabel
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtGui import QMouseEvent
from scipy.constants import milli


class SeekBar(QWidget):
    class ClickableProgressBar(QProgressBar):
        positionChanged = Signal(int)  # Signal emitted when user clicks

        def __init__(self, player: QMediaPlayer, parent=None):
            super().__init__(parent)
            self.wasPlaying = False
            self.player = player
            self.setMinimum(0)
            self.setTextVisible(False)  # Hide the percentage text if not needed
            self.positionChanged.connect(player.setPosition)
            self.player.positionChanged.connect(self.setValue)
            self.player.durationChanged.connect(self.setMaximum)
            self.setFixedHeight(8)
            self.setStyleSheet("""
                QProgressBar::chunk {
                    background-color: #2196F3; /* Solid color */
                    border-radius: 4px;
                    width: 1px; /* Ensures no chunk animation effect */
                }""")

        def updatePosition(self, event: QMouseEvent):
            """Calculate new position and emit signal."""
            click_x = event.position().x()
            progress = max(0, min(click_x / self.width(), 1))
            new_position = int(progress * self.maximum())
            self.positionChanged.emit(new_position)

        def mousePressEvent(self, event: QMouseEvent):
            if event.button() == Qt.LeftButton:
                self._is_dragging = True
                self.wasPlaying = self.player.isPlaying()
                self.player.pause()
                self.updatePosition(event)

        def mouseMoveEvent(self, event: QMouseEvent):
            if self._is_dragging:
                self.updatePosition(event)

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.LeftButton:
                if self.wasPlaying:
                    self.player.play()
                self._is_dragging = False

    def __init__(self, player: QMediaPlayer, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.player = player
        self.curr_time_label = QLabel("-:-:-")
        self.slash_label = QLabel("/")
        self.duration_label = QLabel("-:-:-")
        self.player.positionChanged.connect(self.updateTime)
        self.player.durationChanged.connect(self.updateDuration)
        layout.addWidget(self.curr_time_label)
        layout.addWidget(self.slash_label)
        layout.addWidget(self.duration_label)

        self.progressBar = self.ClickableProgressBar(self.player, parent=self)
        layout.addWidget(self.progressBar)
        self.setLayout(layout)

    @staticmethod
    def format_msec(time_msec):
        total_seconds = time_msec // 1000
        h, remainder = divmod(total_seconds, 3600)
        m, s = divmod(total_seconds, 60)
        return f"{h:02}:{m:02}:{s:02}"

    def updateTime(self, time_msec):
        self.curr_time_label.setText(f"{self.format_msec(time_msec)}")

    def updateDuration(self, new_duration):
        self.duration_label.setText(f"{self.format_msec(new_duration)}")
