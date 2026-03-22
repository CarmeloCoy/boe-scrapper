import os


class Settings:
    """A class to manage application settings."""

    def __getattr__(self, name):
        """Get a setting value by name."""
        if name in self._settings:
            return self._settings[name]
        raise AttributeError(f"Setting '{name}' not found.")

    def __init__(self):
        self._settings = {
            "download_path": os.getenv(
                "DOWNLOAD_PATH",
                "./downloads",
            ),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_file": os.getenv("LOG_FILE", "./logs/boe_scraper.log"),
        }


settings = Settings()
