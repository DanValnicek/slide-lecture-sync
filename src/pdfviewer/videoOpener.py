from PySide6.QtCore import Slot
from PySide6.QtGui import QAction, QIcon

from pyqt5vlc import VideoPlayer


class VideoOpener(QAction):
    def __init__(self, parent):
        super().__init__(parent)
        # icon = QIcon()
        # icon.hasThemeIcon(u"Open video at this slide")
        # self.icon(QIcon())
        self.setText("open video here")
        self.triggered.connect(self.on_triggered)

    @Slot()
    def on_triggered(self):
        print("opening video here")
        player = VideoPlayer()
        player.load_video(
            r"../data/videos/IMS_2024-10-18_1080p.mp4")  # Use raw string for Windows paths
        player.show()
        player.set_time(4994000)
