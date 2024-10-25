def find_input_device_index(p, preferred_device_name="", verbose=False):
    if verbose:
        print(f"Listing input devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0 and "(hw:" in dev["name"]:
                print(f"Device {i}: {dev['name']}")

    if preferred_device_name:
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if (
                preferred_device_name.lower() in dev["name"].lower()
                and "(hw:" in dev["name"]
            ):
                print(f"Found input device: {dev['name']}")
                return i

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev["maxInputChannels"] > 0 and "(hw:" in dev["name"]:
            print(f"Found input device: {dev['name']}")
            return i

    return None


def find_output_device_index(p, preferred_device_name="", verbose=False):
    if verbose:
        print(f"Listing output devices:")
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxOutputChannels"] > 0 and "(hw:" in dev["name"]:
                print(f"Device {i}: {dev['name']}")

    if preferred_device_name:
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if (
                preferred_device_name.lower() in dev["name"].lower()
                and "(hw:" in dev["name"]
            ):
                print(f"Found output device: {dev['name']}")
                return i

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev["maxOutputChannels"] > 0 and "(hw:" in dev["name"]:
            print(f"Found output device: {dev['name']}")
            return i

    return None
