from pathlib import Path

from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtCore import Slot, QUrl
from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox, QHBoxLayout

from src.VideoInfo import PresentationSlideIntervals
from src.videoPlayer.pyqt6_video_player import VideoPlayerWindow


class VideoOpener(QWidget):
    def __init__(self, doc_loc_sig, pdf_view):
        super().__init__(None)
        self.setDisabled(True)
        self.slide_intervals = PresentationSlideIntervals()
        self.video_player = None
        self.pdf_view = pdf_view

        self.open_vid_here_btn = QPushButton("Open video here")
        self.scroll_to_vid_current_slide = QPushButton("To current slide")
        self.follow_vid_checkbox = QCheckBox("Follow video")
        doc_loc_sig.connect(self.document_changed)
        self.open_vid_here_btn.connect(self.open_vid_here)
        self.follow_vid_checkbox.stateChanged.connect(self.folow_video_state_changed)
        self.scroll_to_vid_current_slide.connect(lambda:self.jump_to_slide_at_current_video_position(self.video_player.))

    def init_ui(self):
        layout = QHBoxLayout()
        layout.addWidget(self.open_vid_here_btn)
        layout.addWidget(self.scroll_to_vid_current_slide)
        layout.addWidget(self.follow_vid_checkbox)

        self.setLayout(layout)

    @Slot(QUrl)
    def document_changed(self, location: QUrl):
        self.slide_intervals = PresentationSlideIntervals(Path(location.toLocalFile()))
        if self.slide_intervals.are_empty():
            self.setDisabled(True)
            return
        self.setDisabled(False)
        self.video_player.get_position_changed_signal

    def folow_video_state_changed(self, state):
        if state == Qt.Checked:
            self.jump_to_slide_at_current_video_position.connect(self.video_player.get_position_changed_signal())
        else:
            self.jump_to_slide_at_current_video_position.disconnect(self.video_player.get_position_changed_signal())

    @Slot(int)
    def jump_to_slide_at_current_video_position(self, pos_msec):
        slide_id = self.slide_intervals.get_slide_from_position(pos_msec)
        nav = self.pdf_view.pageNavigator()
        nav.jump(slide_id, QPoint(), nav.currentZoom())

    @Slot()
    def open_vid_here(self):
        slide_id = self.pdf_view.pageNavigator().currentPage()
        slide_intervals = self.slide_intervals.get_intervals(slide_id)
        if slide_intervals is None or len(slide_intervals) == 0:
            self.setEnabled(False)
            QTimer.singleShot(500, lambda: self.setEnabled(True))
            return
        beginning_timestamp = slide_intervals[0][0]
        if self.video_player is None:
            self.video_player = VideoPlayerWindow()
            self.video_player.openWindow()
        self.video_player.seek_position(beginning_timestamp)
