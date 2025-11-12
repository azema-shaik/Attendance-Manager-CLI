# tests/test_config.py
import json
from pathlib import Path
from datetime import datetime, timedelta
import builtins

import pytest

from main import Main

def setup_tmp_main(tmp_path, monkeypatch):
    """
    Create temp Data tree and return (Main instance, main_path, sub_path, cfg_path).
    """
    data_root = tmp_path / "Data"
    overall = data_root / "Overall"
    subj = data_root / "Subject_Data"
    overall.mkdir(parents=True)
    subj.mkdir(parents=True)
    main_path = str(overall / "Attendance")
    sub_path = str(subj)

    # create minimal attendance csv so Extract_data won't blow up if called accidentally
    Path(main_path + ".csv").write_text("Subject,Total Classes,Present,Attendance Percentage,Last Updated\n")

    # avoid interactive Main() call inside __init__
    monkeypatch.setattr(Main, "Main", lambda self: None)
    m = Main(main_path, sub_path)
    cfg_path = Path(main_path).parents[1] / "semester_config.cfg"
    return m, main_path, sub_path, cfg_path

def test__save_semester_future_writes_cfg(tmp_path, monkeypatch):
    m, main_path, sub_path, cfg_path = setup_tmp_main(tmp_path, monkeypatch)

    future_date = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    result = m._save_semester("2025-Fall", future_date)

    assert isinstance(result, dict)
    assert result["semester_id"] == "2025-Fall"
    assert "end_date" in result

    assert cfg_path.exists()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["semester_id"] == "2025-Fall"
    assert len(cfg["end_date"]) == 10 and "-" in cfg["end_date"]

def test__save_semester_past_date_returns_false_and_no_write(tmp_path, monkeypatch):
    m, main_path, sub_path, cfg_path = setup_tmp_main(tmp_path, monkeypatch)

    past_date = (datetime.now() - timedelta(days=10)).strftime("%d/%m/%Y")
    result = m._save_semester("2024-Spring", past_date)

    # should return False and NOT write the config
    assert result is False
    assert (Path(m.main_path).parents[1] / 'semester_config.cfg').exists()

def test_save_semester_config_interactive(tmp_path, monkeypatch):
    m, main_path, sub_path, cfg_path = setup_tmp_main(tmp_path, monkeypatch)

    # provide interactive inputs via monkeypatched input()
    future_date = (datetime.now() + timedelta(days=15)).strftime("%d/%m/%Y")
    inputs = iter(["MySem2025", future_date])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(inputs))

    # call wrapper; it will call _save_semester internally
    m.save_semester_config()

    assert cfg_path.exists()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["semester_id"] == "MySem2025"
    assert cfg["end_date"] == (datetime.strptime(future_date, "%d/%m/%Y")).strftime("%Y-%m-%d")
