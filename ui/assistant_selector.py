from PyQt6.QtWidgets import QWidget, QComboBox, QPushButton, QHBoxLayout, QLabel


class AssistantSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.assistant_combo = QComboBox()
        self.add_button = QPushButton("Add to Chat")

        self.layout.addWidget(QLabel("Select Assistant:"))
        self.layout.addWidget(self.assistant_combo)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

    def update_assistants(self, assistants):
        self.assistant_combo.clear()
        self.assistant_combo.addItems(assistants)
