from PyQt6.QtWidgets import QWidget, QComboBox, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class AssistantSelector(QWidget):
    # Add the signal
    assistant_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        # Set spacing and margins
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.assistant_combo = QComboBox()
        self.add_button = QPushButton("Add to Chat")

        label = QLabel("Select Assistant:")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.layout.addWidget(label)
        self.layout.addWidget(self.assistant_combo)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

        # Connect the add button to emit the signal
        self.add_button.clicked.connect(self._on_add_clicked)

    def update_assistants(self, assistants):
        self.assistant_combo.clear()
        self.assistant_combo.addItems(assistants)

    def _on_add_clicked(self):
        selected = self.assistant_combo.currentText()
        if selected:
            self.assistant_selected.emit(selected)
