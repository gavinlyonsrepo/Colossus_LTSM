# pylint: disable=missing-docstring
import configparser
import colossus_ltsm.settings as settings_module


def test_settings_loads_defaults_when_no_config_exists(tmp_path, monkeypatch):
    config_path = tmp_path / "colossus_ltsm" / "colossus_ltsm.cfg"
    monkeypatch.setattr(settings_module, "CL_CONFIG_PATH", config_path)
    settings = settings_module.Settings()

    assert settings.getint("display", "scale", fallback=4) == 4
    assert settings.getbool("debug", "debugOnOff", fallback=True) is True
    assert settings.getstr("paths", "input_dir", fallback=".") == "."


def test_settings_save_and_reload_writes_config(tmp_path, monkeypatch):
    config_path = tmp_path / "colossus_ltsm" / "colossus_ltsm.cfg"
    monkeypatch.setattr(settings_module, "CL_CONFIG_PATH", config_path)
    settings = settings_module.Settings()

    settings.set("display", "scale", 12)
    settings.set("debug", "debugOnOff", 1)
    settings.set("paths", "output_dir", "/tmp")

    parser = configparser.ConfigParser()
    parser.read(config_path)

    assert parser.getint("display", "scale") == 12
    assert parser.getboolean("debug", "debugOnOff") is True
    assert parser.get("paths", "output_dir") == "/tmp"
