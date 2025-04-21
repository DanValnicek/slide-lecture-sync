from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QFileDialog, QProgressBar, QVBoxLayout, QPushButton
from pathlib import Path

from src.videoImgExtraction import SlideIntervalFinder


class VideoPresentationProcessingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.out_pdf_path = ""
        self.video_path = ""
        self.pdf_path = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)

        self.select_video_btn = QPushButton("Select Video")
        self.select_pdf_btn = QPushButton("Select PDF")
        self.select_out_pdf_btn = QPushButton("Select PDF")
        self.start_btn = QPushButton("Start Processing")

        self.select_video_btn.clicked.connect(self.select_video)
        self.select_pdf_btn.clicked.connect(self.select_pdf)
        self.select_out_pdf_btn.clicked.connect(self.select_out_pdf)
        self.start_btn.clicked.connect(self.start_processing)

        layout.addWidget(self.select_video_btn)
        layout.addWidget(self.select_pdf_btn)
        layout.addWidget(self.select_out_pdf_btn)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle("Video & PDF Processor")

    def select_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.avi *.mkv)")
        if file_name:
            self.video_path = Path(file_name)
            self.select_video_btn.setText(f"Video: {file_name}")

    def select_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.pdf_path = Path(file_name)
            self.select_pdf_btn.setText(f"PDF: {file_name}")

    def select_out_pdf(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Select output PDF", "", "PDF Files (*.pdf)")
        if file_name:
            self.out_pdf_path = Path(file_name)
            self.select_out_pdf_btn.setText(f"PDF: {file_name}")

    def start_processing(self):
        self.progress_bar.setRange(0, 0)
        if not self.video_path or not self.pdf_path or not self.out_pdf_path:
            self.progress_bar.setMaximum(1)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Please select all files")
            self.progress_bar.repaint()
            return
        self.progress_bar.setFormat("Processing in progress")
        self.progress_bar.repaint()
        self.start_btn.setDisabled(True)
        self.select_video_btn.setDisabled(True)
        self.select_pdf_btn.setDisabled(True)
        self.select_out_pdf_btn.setDisabled(True)

        self.worker = SlideIntervalFinder(self.video_path, self.pdf_path, self.out_pdf_path)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.worker.get_frame_cnt())
        self.worker.progres_updated.connect(self.progress_bar.setValue)
        self.worker.finished.connect(lambda: self.progress_bar.setFormat("Processing Complete"))
        self.worker.start()

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()
        event.accept()
