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
import traceback


class AudioControls(QWidget):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    input_device_changed = pyqtSignal(int)
    output_device_changed = pyqtSignal(int)

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
        devices_layout = QVBoxLayout()

        # Input device selection
        input_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        self.input_combo.currentIndexChanged.connect(self._on_input_device_changed)
        input_layout.addWidget(QLabel("Input Device:"))
        input_layout.addWidget(self.input_combo, stretch=1)

        # Output device selection
        output_layout = QHBoxLayout()
        self.output_combo = QComboBox()
        self.output_combo.currentIndexChanged.connect(self._on_output_device_changed)
        output_layout.addWidget(QLabel("Output Device:"))
        output_layout.addWidget(self.output_combo, stretch=1)

        devices_layout.addLayout(input_layout)
        devices_layout.addLayout(output_layout)

        # Audio level indicator
        self.level_indicator = QProgressBar()
        self.level_indicator.setRange(0, 100)
        self.level_indicator.setTextVisible(False)
        self.level_indicator.setFixedHeight(10)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self._on_record_clicked)

        # Play button
        self.play_button = QPushButton("Play Recording")
        self.play_button.clicked.connect(self._on_play_clicked)
        self.play_button.setEnabled(False)

        controls_layout.addWidget(self.record_button)
        controls_layout.addWidget(self.play_button)

        layout.addLayout(devices_layout)
        layout.addWidget(self.level_indicator)
        layout.addLayout(controls_layout)

        # Timer for updating audio level - increase interval to reduce load
        self._level_timer = QTimer()
        self._level_timer.timeout.connect(self._update_audio_level)
        self._level_timer.setInterval(100)  # Update every 100ms instead of 200ms

    def _load_devices(self):
        devices = self._provider.get_devices()
        default_input_name = None
        default_output_name = None

        try:
            registry = ProviderRegistry.get_instance()
            config = registry.get_provider_config(AudioInputProvider)
            default_input_name = config.get("input_device")
            default_output_name = config.get("output_device")
        except Exception as e:
            print(f"!!! Error getting device config: {e}")

        # Load input devices
        input_devices = devices.get("input", [])
        default_input_index = 0
        for i, device in enumerate(input_devices):
            self.input_combo.addItem(device["name"], device["id"])
            if default_input_name and default_input_name in device["name"]:
                default_input_index = i

        if self.input_combo.count() > 0:
            self.input_combo.setCurrentIndex(default_input_index)
            print(f">>> Using input device: {self.input_combo.currentText()}")

        # Load output devices
        output_devices = devices.get("output", [])
        default_output_index = 0
        for i, device in enumerate(output_devices):
            self.output_combo.addItem(device["name"], device["id"])
            if default_output_name and default_output_name in device["name"]:
                default_output_index = i

        if self.output_combo.count() > 0:
            self.output_combo.setCurrentIndex(default_output_index)
            print(f">>> Using output device: {self.output_combo.currentText()}")

    def _on_input_device_changed(self, index: int):
        if index >= 0:
            device_id = self.input_combo.currentData()
            self.input_device_changed.emit(device_id)

    def _on_output_device_changed(self, index: int):
        if index >= 0:
            device_id = self.output_combo.currentData()
            self.output_device_changed.emit(device_id)

    def _on_record_clicked(self, checked: bool):
        self._recording = checked
        self.record_button.setText("Stop Recording" if checked else "Start Recording")
        self.play_button.setEnabled(not checked)

        if checked:
            print("\n=== Starting audio recording ===")
            try:
                device_id = self.input_combo.currentData()
                devices = self._provider.get_devices()
                input_devices = devices.get("input", [])
                device_info = next(d for d in input_devices if d["id"] == device_id)

                config = AudioConfig(
                    sample_rate=int(device_info["sample_rate"]),
                    channels=1,
                    chunk_size=1024,
                    device_id=device_id,
                )
                print(f">>> Audio config: {config}")

                self._provider.start_stream(config)
                self._level_timer.start()
                self.recording_started.emit()

            except Exception as e:
                print(f"!!! Error starting recording: {str(e)}")
                print(traceback.format_exc())
                self._recording = False
                self.record_button.setChecked(False)
                return
        else:
            print("\n=== Stopping audio recording ===")
            self._level_timer.stop()
            self._provider.stop_stream()
            self.level_indicator.setValue(0)
            self.recording_stopped.emit()
            self.play_button.setEnabled(True)

    def _on_play_clicked(self):
        print("\n=== Playing recorded audio ===")
        try:
            self.play_button.setEnabled(False)
            self.record_button.setEnabled(False)

            # Get output device ID
            output_device_id = self.output_combo.currentData()
            print(f">>> Using output device ID: {output_device_id}")

            # Play the recorded audio
            self._provider.play_audio(None)

            self.play_button.setEnabled(True)
            self.record_button.setEnabled(True)
        except Exception as e:
            print(f"!!! Error playing audio: {str(e)}")
            print(traceback.format_exc())
            self.play_button.setEnabled(True)
            self.record_button.setEnabled(True)

    def _update_audio_level(self):
        if not self._recording:
            return

        try:
            chunk = self._provider.read_chunk()
            if not chunk:
                return

            audio_data = np.frombuffer(chunk, dtype=np.int16)
            if len(audio_data) == 0:
                return

            max_value = np.max(np.abs(audio_data))
            level = int((max_value / 32768.0) * 100)
            self.level_indicator.setValue(level)

        except Exception as e:
            print(f"!!! Error reading audio chunk: {str(e)}")
            print(traceback.format_exc())

    def is_recording(self) -> bool:
        return self._recording
