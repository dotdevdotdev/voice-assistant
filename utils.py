import pyaudio


def find_input_device_index(p, preferred_device_name="", verbose=False):
    if verbose:
        print(f"Listing input devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0 and "(hw:" in dev["name"]:
                try:
                    if p.is_format_supported(
                        rate=44100,
                        input_device=i,
                        input_channels=1,
                        input_format=pyaudio.paInt16,
                        output_device=None,
                        output_channels=None,
                        output_format=None,
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
                        input_device=i,
                        input_channels=1,
                        input_format=pyaudio.paInt16,
                        output_device=None,
                        output_channels=None,
                        output_format=None,
                    ):
                        print(f"Found input device: {dev['name']}")
                        return i
                except ValueError:
                    continue

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev["maxInputChannels"] > 0 and "(hw:" in dev["name"]:
            try:
                if p.is_format_supported(
                    rate=44100,
                    input_device=i,
                    input_channels=1,
                    input_format=pyaudio.paInt16,
                    output_device=None,
                    output_channels=None,
                    output_format=None,
                ):
                    print(f"Found input device: {dev['name']}")
                    return i
            except ValueError:
                continue

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
