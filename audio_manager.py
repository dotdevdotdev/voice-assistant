class AudioManager:
    def __init__(self, app_settings):
        self.logger = logging.getLogger(__name__)
        self.pyaudio = pyaudio.PyAudio()

        # Store device preferences
        self.preferred_input = app_settings["app"].get("input_device", None)
        self.preferred_output = app_settings["app"].get("output_device", None)

        # Initialize devices
        self.input_device_index = self._initialize_input_device()
        self.output_device_index = self._initialize_output_device()

        # Validate format support
        self._validate_audio_format()

    def _initialize_input_device(self):
        """Initialize and validate input device"""
        device_index = find_input_device_index(
            self.pyaudio, preferred_device_name=self.preferred_input, verbose=True
        )
        if device_index is None:
            raise ValueError("No valid input device found")
        return device_index

    def _initialize_output_device(self):
        """Initialize and validate output device"""
        device_index = find_output_device_index(
            self.pyaudio, preferred_device_name=self.preferred_output, verbose=True
        )
        if device_index is None:
            raise ValueError("No valid output device found")
        return device_index

    def _validate_audio_format(self):
        """Validate audio format support for both devices"""
        try:
            if not self.pyaudio.is_format_supported(
                rate=44100,
                input_device=self.input_device_index,
                input_channels=1,
                input_format=pyaudio.paFloat32,
                output_device=self.output_device_index,
                output_channels=1,
                output_format=pyaudio.paFloat32,
            ):
                raise ValueError("Audio format not supported by devices")
        except ValueError as e:
            self.logger.error(f"Audio format validation failed: {e}")
            raise

    def get_pyaudio(self):
        """Get PyAudio instance"""
        return self.pyaudio

    def get_device_indices(self):
        """Get current device indices"""
        return self.input_device_index, self.output_device_index

    def __del__(self):
        """Cleanup PyAudio resources"""
        if hasattr(self, "pyaudio"):
            try:
                self.pyaudio.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating PyAudio: {e}")
