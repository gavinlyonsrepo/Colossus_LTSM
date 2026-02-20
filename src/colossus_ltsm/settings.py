"""
This module handles application settings using a configuration file.
It provides methods to load, save, and access settings with defaults.
"""
import configparser
from pathlib import Path

CL_CONFIG_PATH = Path.home() / ".config" / "colossus_ltsm" / "colossus_ltsm.cfg"

CL_DEFAULTS_DISPLAY = {
	"scale": "4",
	"cols": "16"
}

CL_DEFAULTS_DEBUG = {
	"debugOnOff": "0"
}


class Settings:
	"""Singleton class to manage application settings."""

	def __init__(self):
		self.config = configparser.ConfigParser()
		self.load()

	def load(self):
		"""Load settings from the config file, or use defaults."""
		try:
			if CL_CONFIG_PATH.exists():
				self.config.read(CL_CONFIG_PATH)

			# --- Display Section ---
			if "Display" not in self.config:
				self.config["Display"] = CL_DEFAULTS_DISPLAY.copy()
			else:
				for key, val in CL_DEFAULTS_DISPLAY.items():
					self.config["Display"].setdefault(key, val)

			# --- Debug Section ---
			if "Debug" not in self.config:
				self.config["Debug"] = CL_DEFAULTS_DEBUG.copy()
			else:
				for key, val in CL_DEFAULTS_DEBUG.items():
					self.config["Debug"].setdefault(key, val)

			# Create file if it doesn't exist
			if not CL_CONFIG_PATH.exists():
				print("[Settings] Config file not found, creating with defaults.")
				self.save()

		except Exception as e:
			print(f"[Settings] Error loading config: {e}, using defaults")
			self.config["Display"] = CL_DEFAULTS_DISPLAY.copy()
			self.config["Debug"] = CL_DEFAULTS_DEBUG.copy()

	def save(self):
		"""Save the current settings to the config file."""
		try:
			CL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
			with CL_CONFIG_PATH.open("w") as f:
				self.config.write(f)
		except Exception as e:
			print(f"[Settings] Error saving config: {e}")

	def getint(self, section, option, fallback):
		"""Get an integer setting with a fallback value."""
		try:
			return self.config.getint(section, option, fallback=fallback)
		except Exception:
			return fallback

	def getbool(self, section, option, fallback=False):
		"""Get a boolean setting (0/1 or true/false)."""
		try:
			return self.config.getboolean(section, option, fallback=fallback)
		except Exception:
			return fallback

	def set(self, section, option, value):
		"""Set a config value and save."""
		if section not in self.config:
			self.config[section] = {}
		self.config[section][option] = str(value)
		self.save()


# create settings instance singleton.
settings = Settings()

if __name__ == "__main__":
	print("This is a module, not a standalone script.")
else:
	print("Settings module loaded.")