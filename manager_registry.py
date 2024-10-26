class ManagerRegistry:
    _instance = None

    def __init__(self):
        self.audio_manager = None
        self.va_manager = None
        self.ui_manager = None
        # etc...

    @staticmethod
    def get_instance():
        if ManagerRegistry._instance is None:
            ManagerRegistry._instance = ManagerRegistry()
        return ManagerRegistry._instance
