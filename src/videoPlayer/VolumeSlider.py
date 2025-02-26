from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput
from PySide6.QtWidgets import QSlider, QHBoxLayout, QLabel, QPushButton


class VolumeSlider(QtWidgets.QWidget):
    class Slider(QSlider):
        # Signal that emits the normalized volume (0.0 - 1.0)
        value_changed_normalized = Signal(float)

        def __init__(self, audioOut: QAudioOutput):
            super().__init__()
            self._audio_out = audioOut
            self.setOrientation(Qt.Orientation.Horizontal)
            self.setMinimum(0)
            self.setMaximum(100)

            # Apply custom styles
            self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #ddd;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;  /* Color up to the handle */
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #ddd;  /* Color after the handle */
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #2196F3;
                width: 9px;
                margin: -3px 0;
                border-radius: 8px;
            }
        """)

            self.setToolTip("Volume")

            # Initialize the slider to match the audio output's volume
            self.blockSignals(True)  # Prevent emitting while setting initial value
            self.setValue(int(self._audio_out.volume() * 100))
            self.blockSignals(False)

            # Connect signals to update both the slider and audio output
            self.valueChanged.connect(self.on_slider_moved)
            self._audio_out.volumeChanged.connect(self.on_volume_changed)

        def on_slider_moved(self, value):
            """Triggered when the user moves the slider. Updates _audio_out's volume."""
            normalized_value = value / 100.0
            self._audio_out.setVolume(normalized_value)
            self.value_changed_normalized.emit(normalized_value)

        def on_volume_changed(self, value):
            """Triggered when the audio output's volume changes. Updates the slider."""
            self.blockSignals(True)
            percentage = int(value * 100)
            self.setValue(percentage)
            self.setToolTip(f"{percentage}%")
            self.blockSignals(False)

    def __init__(self, audio_out: QAudioOutput, parent=None):
        super().__init__(parent)
        self.slider = self.Slider(audio_out)
        self._audio_out = audio_out
        layout = QHBoxLayout()
        # layout.setSpacing(0)
        layout.totalMaximumSize()
        layout.addWidget(self.slider)
        # Set slider width relative to screen size
        available_width = self.screen().availableGeometry().width()
        self.setFixedWidth(available_width / 15)

        icon = QIcon.fromTheme(QIcon.ThemeIcon.AudioVolumeHigh)
        self.mute_button = QPushButton()
        self.mute_button.setIcon(icon)
        self.mute_button.setFixedWidth(20)
        layout.addWidget(self.mute_button)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.setLayout(layout)
        self._audio_out.volumeChanged.connect(self.update_mute_icon)
        self._audio_out.mutedChanged.connect(self.setMutedIcon)

    def toggle_mute(self):
        """Toggle mute on the audio output and update the icon."""
        if self._audio_out.isMuted():
            self._audio_out.setMuted(False)
        else:
            self._audio_out.setMuted(True)

    def setMutedIcon(self, state):
        if state:
            self.update_mute_icon(0)
        else:
            self.update_mute_icon(self._audio_out.volume())

    def update_mute_icon(self, volume):
        """Update the mute button icon based on volume and mute state."""
        if self._audio_out.isMuted() or volume == 0:
            icon = QIcon.fromTheme("audio-volume-muted")  # Muted icon
        elif volume < 0.3:
            icon = QIcon.fromTheme("audio-volume-low")  # Low volume icon
        elif volume < 0.7:
            icon = QIcon.fromTheme("audio-volume-medium")  # Medium volume icon
        else:
            icon = QIcon.fromTheme("audio-volume-high")  # High volume icon
        self.mute_button.setIcon(icon)
