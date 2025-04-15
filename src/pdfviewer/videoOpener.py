from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtCore import Slot, QUrl
from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox, QSizePolicy, QVBoxLayout

from src.VideoInfo import PresentationSlideIntervals
from src.pdfviewer.ScrollableButtonList import ButtonListWidget
from src.videoPlayer.pyqt6_video_player import VideoPlayerWindow
from src.utils import ms_to_hms
from functools import partial


class VideoOpener(QWidget):
    def __init__(self, doc_loc_sig, pdf_view):
        super().__init__(None)
        self.setDisabled(True)
        self.slide_intervals = PresentationSlideIntervals()
        self.video_player = None
        self.pdf_view = pdf_view

        self.slide_intervals_btns = ButtonListWidget()
        self.scroll_to_vid_current_slide = QPushButton("To current slide")
        self.follow_vid_checkbox = QCheckBox("Follow video")
        doc_loc_sig.connect(self.document_changed)
        self.follow_vid_connected = False
        self.init_ui()
        self.pdf_view.pageNavigator().currentPageChanged.connect(self.make_page_buttons)

    def init_ui(self):

        # self.open_vid_here_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.scroll_to_vid_current_slide.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        layout = QVBoxLayout()
        # layout.addWidget(self.open_vid_here_btn)
        layout.addWidget(self.scroll_to_vid_current_slide)
        layout.addWidget(self.follow_vid_checkbox)
        layout.addWidget(self.slide_intervals_btns)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    @Slot(QUrl)
    def document_changed(self, location: QUrl):
        self.slide_intervals = PresentationSlideIntervals(Path(location.toLocalFile()))
        if self.slide_intervals.are_empty():
            self.setDisabled(True)
            return
        self.setDisabled(False)

    def folow_video_state_changed(self, state):
        if state == Qt.Checked.value:
            if self.follow_vid_connected or self.video_player is None:
                return
            self.video_player.get_position_changed_signal.connect(self.jump_to_slide_at_current_video_position)
            self.follow_vid_connected = True
        else:
            if not self.follow_vid_connected or self.video_player is None:
                return
            self.video_player.get_position_changed_signal.disconnect(self.jump_to_slide_at_current_video_position)
            self.follow_vid_connected = False

    @Slot(int)
    def jump_to_slide_at_current_video_position(self, pos_msec):
        slide_id = self.slide_intervals.get_slide_from_position(pos_msec)
        if slide_id is None:
            return
        nav = self.pdf_view.pageNavigator()
        nav.jump(slide_id, QPoint(), nav.currentZoom())

    def open_vid_here(self, timestamp):
        if self.video_player is None:
            self.video_player_setup()
        self.video_player.seek_position(timestamp)

    def video_player_setup(self):
        self.video_player = VideoPlayerWindow()
        self.video_player.openWindow()
        self.video_player.destroyed.connect(self.video_player_destroyed)
        self.follow_vid_checkbox.stateChanged.connect(self.folow_video_state_changed)
        self.scroll_to_vid_current_slide.clicked.connect(
            lambda: self.jump_to_slide_at_current_video_position(self.video_player.get_video_position())
        )
        self.follow_vid_checkbox.setDisabled(False)
        self.scroll_to_vid_current_slide.setDisabled(False)

    def video_player_destroyed(self):
        self.video_player = None
        self.follow_vid_checkbox.setDisabled(True)
        self.scroll_to_vid_current_slide.setDisabled(True)

    @Slot(int)
    def make_page_buttons(self, page_num):
        slide_intervals = self.slide_intervals.get_intervals(page_num)
        self.slide_intervals_btns.remove_all_buttons()
        if slide_intervals is None or len(slide_intervals) == 0:
            return
        for interval in slide_intervals:
            self.slide_intervals_btns.add_button(
                f"{ms_to_hms(interval[0])} - {ms_to_hms(interval[1])}",
                partial(self.open_vid_here, interval[0])
            )
