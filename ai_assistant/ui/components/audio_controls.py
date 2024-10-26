from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from core.interfaces.audio import AudioInputProvider
from utils.registry import ProviderRegistry


class AudioControls(QWidget):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    device_changed = pyqtSignal(int)  # device_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider = ProviderRegistry.get_instance().get_provider(
            AudioInputProvider
        )
        self._recording = False
        self._setup_ui()
        self._load_devices()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Device selection
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        device_layout.addWidget(QLabel("Input Device:"))
        device_layout.addWidget(self.device_combo, stretch=1)

        # Audio level indicator
        self.level_indicator = QProgressBar()
        self.level_indicator.setRange(0, 100)
        self.level_indicator.setTextVisible(False)
        self.level_indicator.setFixedHeight(10)

        # Recording controls
        controls_layout = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self._on_record_clicked)
        controls_layout.addWidget(self.record_button)

        layout.addLayout(device_layout)
        layout.addWidget(self.level_indicator)
        layout.addLayout(controls_layout)

        # Timer for updating audio level
        self._level_timer = QTimer()
        self._level_timer.timeout.connect(self._update_audio_level)
        self._level_timer.setInterval(100)  # Update every 100ms

    def _load_devices(self):
        devices = self._provider.get_devices()
        for device in devices:
            self.device_combo.addItem(device["name"], device["id"])

    def _on_device_changed(self, index: int):
        if index >= 0:
            device_id = self.device_combo.currentData()
            self.device_changed.emit(device_id)

    def _on_record_clicked(self, checked: bool):
        self._recording = checked
        self.record_button.setText("Stop Recording" if checked else "Start Recording")

        if checked:
            self._level_timer.start()
            self.recording_started.emit()
        else:
            self._level_timer.stop()
            self.level_indicator.setValue(0)
            self.recording_stopped.emit()

    def _update_audio_level(self):
        if self._recording:
            # This would need to be implemented to get actual audio levels
            # For now, just simulate some activity
            import random

            self.level_indicator.setValue(random.randint(0, 100))

    def is_recording(self) -> bool:
        return self._recording
