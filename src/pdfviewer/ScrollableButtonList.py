from PySide6.QtGui import Qt
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QScrollArea


class ButtonListWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Scrollable Button List")

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area setup
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Container widget inside scroll area
        self.scroll_widget = QWidget()
        self.scroll_widget.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)
        self.scroll_widget.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.buttons = {}  # Store button references

    def add_button(self, value, action_function):
        button = QPushButton(f"{value}")
        button.clicked.connect(action_function)
        self.scroll_layout.addWidget(button)
        self.buttons[value] = button

    def remove_all_buttons(self):
        for button in self.buttons.values():
            self.scroll_layout.removeWidget(button)
            button.deleteLater()
        self.buttons.clear()

    def remove_button(self, value):
        if value in self.buttons:
            button = self.buttons.pop(value)
            self.scroll_layout.removeWidget(button)
            button.deleteLater()
