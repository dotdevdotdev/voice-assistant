import pyaudio
import logging


def find_input_device_index(audio):
    """Find suitable input device with validation"""
    logger = logging.getLogger(__name__)

    try:
        # First, try to find a device that explicitly supports our needs
        for i in range(audio.get_device_count()):
            try:
                device_info = audio.get_device_info_by_index(i)
                logger.debug(f"Checking device {i}: {device_info['name']}")

                # Skip devices with no input channels
                if device_info.get("maxInputChannels", 0) <= 0:
                    logger.debug(f"Device {i} has no input channels, skipping")
                    continue

                # Get supported rates
                try:
                    supported_rates = [
                        int(rate)
                        for rate in [8000, 16000, 44100, 48000]
                        if audio.is_format_supported(
                            rate,
                            input_device=i,
                            input_channels=1,
                            input_format=pyaudio.paFloat32,
                        )
                    ]
                    if supported_rates:
                        logger.info(
                            f"Device {i} ({device_info['name']}) supports rates: {supported_rates}"
                        )
                        return i
                except Exception as e:
                    logger.debug(f"Error checking rates for device {i}: {e}")
                    continue

            except Exception as e:
                logger.debug(f"Error checking device {i}: {e}")
                continue

        # If no perfect match, try to find any working input device
        logger.warning("No ideal device found, trying fallback options")
        for i in range(audio.get_device_count()):
            try:
                device_info = audio.get_device_info_by_index(i)
                if device_info.get("maxInputChannels", 0) > 0:
                    logger.info(f"Using fallback device {i}: {device_info['name']}")
                    return i
            except:
                continue

        logger.error("No working input device found")
        return None

    except Exception as e:
        logger.error(f"Error finding input device: {e}")
        return None


def find_output_device_index(p, preferred_device_name="", verbose=False):
    if verbose:
        print(f"Listing output devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxOutputChannels"] > 0 and "(hw:" in dev["name"]:
                try:
                    if p.is_format_supported(
                        rate=44100,
                        input_device=None,
                        input_channels=None,
                        input_format=None,
                        output_device=i,
                        output_channels=1,
                        output_format=pyaudio.paInt16,
                    ):
                        print(f"Device {i}: {dev['name']}")
                except ValueError:
                    continue

    if preferred_device_name:
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if (
                preferred_device_name.lower() in dev["name"].lower()
                and "(hw:" in dev["name"]
            ):
                try:
                    if p.is_format_supported(
                        rate=44100,
                        input_device=None,
                        input_channels=None,
                        input_format=None,
                        output_device=i,
                        output_channels=1,
                        output_format=pyaudio.paInt16,
                    ):
                        print(f"Found output device: {dev['name']}")
                        return i
                except ValueError:
                    continue

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev["maxOutputChannels"] > 0 and "(hw:" in dev["name"]:
            try:
                if p.is_format_supported(
                    rate=44100,
                    input_device=None,
                    input_channels=None,
                    input_format=None,
                    output_device=i,
                    output_channels=1,
                    output_format=pyaudio.paInt16,
                ):
                    print(f"Found output device: {dev['name']}")
                    return i
            except ValueError:
                continue

    return None
