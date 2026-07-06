import threading
import dotenv


class Context(dict):
    """A context class that can be used to store and 
    retrieve data in a thread-safe manner."""

    lock: threading.Lock = threading.Lock()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        dotenv.load_dotenv('.env')
        # Load environment variables from .env file
        # into the context dictionary
        for key, value in dotenv.dotenv_values('.env').items():
            if key.upper():
                self[key] = value

    def __getitem__(self, key):
        with self.lock:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        with self.lock:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        with self.lock:
            super().__delitem__(key)
