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
from core.interfaces.audio import AudioInputProvider, AudioConfig
from utils.registry import ProviderRegistry
import numpy as np


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

        # Timer for updating audio level - increase interval to reduce load
        self._level_timer = QTimer()
        self._level_timer.timeout.connect(self._update_audio_level)
        self._level_timer.setInterval(200)  # Update every 200ms instead of 100ms

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
            print("Starting audio recording...")
            try:
                # Get current device info
                device_id = self.device_combo.currentData()
                device_info = self._provider.get_devices()[
                    self.device_combo.currentIndex()
                ]
                sample_rate = int(device_info["sample_rate"])

                print(
                    f"Using device: {device_info['name']} with sample rate: {sample_rate}"
                )

                config = AudioConfig(
                    sample_rate=sample_rate,  # Use device's sample rate directly
                    channels=1,
                    chunk_size=1024,
                    device_id=device_id,
                )
                print(f"Using audio config: {config}")
                self._provider.start_stream(config)
                print("Audio stream started successfully")
                self._level_timer.start()
                self.recording_started.emit()
            except Exception as e:
                print(f"Error starting audio stream: {e}")
                self.record_button.setChecked(False)
                return
        else:
            print("Stopping audio recording...")
            self._level_timer.stop()
            self._provider.stop_stream()
            self.level_indicator.setValue(0)
            self.recording_stopped.emit()

    def _update_audio_level(self):
        if self._recording:
            try:
                chunk = self._provider.read_chunk()
                print(f"Read audio chunk of size: {len(chunk)} bytes")
                # Convert to numpy array for level calculation
                audio_data = np.frombuffer(chunk, dtype=np.float32)
                level = int(np.abs(audio_data).mean() * 100)
                self.level_indicator.setValue(level)
            except Exception as e:
                print(f"Error reading audio chunk: {e}")

    def is_recording(self) -> bool:
        return self._recording
