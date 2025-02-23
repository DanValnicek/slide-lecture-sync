import os
import sys
from os import path

import vlc
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QSlider, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtGui import QKeySequence, QAction


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PyQt5 VLC Player')
        self.setGeometry(100, 100, 800, 600)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Debug Label (Shows the video file path)
        # self.debug_label = QLabel("No video loaded", self)
        # self.debug_label.setStyleSheet("color: red; font-size: 14px;")  # Styling for visibility
        # self.main_layout.addWidget(self.debug_label)

        # Video Widget
        self.video_widget = QWidget(self)
        self.main_layout.addWidget(self.video_widget, stretch=1)  # Video widget takes most of the space

        # Set the video widget to the media player
        if sys.platform == "win32":  # Windows
            self.media_player.set_hwnd(self.video_widget.winId())
        elif sys.platform == "darwin":  # macOS
            self.media_player.set_nsobject(int(self.video_widget.winId()))
        else:  # Linux
            self.media_player.set_xwindow(self.video_widget.winId())

        # Controls Layout (at the bottom)
        self.controls_layout = QVBoxLayout()

        # Seek Bar
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self.set_position)
        self.seek_slider.enterEvent = self.show_time_on_hover
        self.controls_layout.addWidget(self.seek_slider)

        # Play/Pause Button and Volume Control
        self.bottom_controls_layout = QHBoxLayout()

        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.play_pause)
        self.bottom_controls_layout.addWidget(self.play_button)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.media_player.audio_get_volume())
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.bottom_controls_layout.addWidget(self.volume_slider)

        self.controls_layout.addLayout(self.bottom_controls_layout)

        # Playback Speed Control
        self.speed_layout = QHBoxLayout()
        self.speed_label = QLabel('Playback Speed: 1.0x')
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.set_speed)
        self.speed_layout.addWidget(self.speed_label)
        self.speed_layout.addWidget(self.speed_slider)
        self.controls_layout.addLayout(self.speed_layout)

        # Add controls layout to the main layout
        self.main_layout.addLayout(self.controls_layout)

        # Timer to update the seek bar
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)

        # Shortcuts
        self.shortcut_play_pause = QAction(self)
        self.shortcut_play_pause.setShortcut(QKeySequence(Qt.Key_Space))
        self.shortcut_play_pause.triggered.connect(self.play_pause)
        self.addAction(self.shortcut_play_pause)

        # Pause on click anywhere on the screen
        self.central_widget.mousePressEvent = self.pause_on_click

    def play_pause(self):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_button.setText('Play')
        else:
            self.media_player.play()
            self.play_button.setText('Pause')

    def set_volume(self, volume):
        self.media_player.audio_set_volume(volume)

    def set_speed(self, speed):
        self.media_player.set_rate(speed / 100)
        self.speed_label.setText(f'Playback Speed: {speed / 100:.1f}x')

    def set_position(self, position):
        self.media_player.set_position(position / 1000)

    def set_time(self, time_ms):
        self.media_player.set_time(time_ms)

    def update_ui(self):
        if self.media_player.is_playing():
            self.seek_slider.setValue(int(self.media_player.get_position() * 1000))

    def show_time_on_hover(self, event):
        if self.media_player.is_playing():
            time = self.media_player.get_time()
            self.seek_slider.setToolTip(f'{time // 60000:02}:{(time % 60000) // 1000:02}')

    def pause_on_click(self, event):
        if self.media_player.is_playing():
            self.media_player.pause()
            self.play_button.setText('Play')

    def load_video(self, file_path):
        # Ensure valid file path and normalize it
        file_path = os.path.abspath(file_path)

        # Update the debug label to show the video path
        # self.debug_label.setText(f"Loaded: {file_path}")

        print(f"Loading video: {file_path}")  # Console Debugging

        media = self.instance.media_new(file_path)
        self.media_player.set_media(media)
        self.media_player.play()
        self.play_button.setText('Pause')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # video_path = os.path.normpath(sys.argv[1])
    video_path = None
    player = VideoPlayer()
    player.load_video(video_path)  # Use raw string for Windows paths
    player.show()
    sys.exit(app.exec_())
