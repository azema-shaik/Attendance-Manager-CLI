import json
from pathlib import Path
import pandas as pd
import pytest
from datetime import datetime, timedelta
from main import Main

# helper to setup temp Data structure
def setup_tmp_data(tmp_path):
    data_root = tmp_path / "Data"
    overall = data_root / "Overall"
    subj = data_root / "Subject_Data"
    overall.mkdir(parents=True)
    subj.mkdir(parents=True)
    main_path = str(overall / "Attendance")           # will create Attendance.csv
    sub_path = str(subj)
    # create attendance csv with a single subject row
    att_df = pd.DataFrame([{
        "Subject": "Math",
        "Total Classes": 1,
        "Present": 1,
        "Attendance Percentage": 100.0,
        "Last Updated": ""
    }])
    att_df.to_csv(main_path + ".csv", index=False)
    # create subject file
    sub_df = pd.DataFrame([{"Lec_Date": "Wed Nov 12 2025", "Status": True}])
    sub_df.to_csv(subj / "Math.csv", index=False)
    return main_path, sub_path, data_root

@pytest.fixture
def main_instance(tmp_path, monkeypatch):
    # prepare data
    main_path, sub_path, data_root = setup_tmp_data(tmp_path)
    # monkeypatch Main.Main to no-op to avoid interactive loop on __init__
    monkeypatch.setattr(Main, "Main", lambda self: None)
    m = Main(main_path, sub_path)
    return m, main_path, sub_path, data_root

def test_archive_dry_run_and_real(main_instance):
    m, main_path, sub_path, data_root = main_instance
    semester_id = "test-sem"

    # dry-run should return planned dict and not remove files
    dr = m.archive_semester(semester_id, archive=True, dry_run=True)
    assert isinstance(dr, dict)
    assert dr.get("status") == "dry_run"
    assert "planned" in dr
    # original files still present
    assert Path(main_path + ".csv").exists()
    assert (Path(sub_path) / "Math.csv").exists()

    # create a config file (optional), with a past end_date so prompt would consider it ended
    cfg_path = Path(main_path).parents[1] / "semester_config.cfg"
    cfg = {
        "semester_id": semester_id,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    cfg_path.write_text(json.dumps(cfg))

    # real archive -- should succeed and create zip
    res = m.archive_semester(semester_id, archive=True, dry_run=False)
    assert isinstance(res, dict)
    assert res.get("status") == "ok"
    archive_file = Path(main_path).parents[1] / "archives" / f"{semester_id}.zip"
    assert archive_file.exists()

    # skeleton CSVs recreated
    assert Path(main_path + ".csv").exists()
    assert (Path(sub_path) / "Math.csv").exists()

    # archive contains expected files (check basenames)
    import zipfile
    with zipfile.ZipFile(archive_file, "r") as zf:
        names = {Path(x).name for x in zf.namelist()}
    assert {"Attendance.csv", "Math.csv"} <= names

def test_load_semester_config_and_has_ended(tmp_path, monkeypatch):
    # setup data & instance
    main_path, sub_path, data_root = setup_tmp_data(tmp_path)
    monkeypatch.setattr(Main, "Main", lambda self: None)
    m = Main(main_path, sub_path)

    cfg_path = Path(main_path).parents[1] / "semester_config.cfg"

    # no config -> load returns None
    if cfg_path.exists():
        cfg_path.unlink()
    assert m.load_semester_config() is None

    # write a future config and test has_semester_ended False
    future_cfg = {
        "semester_id": "fut",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    }
    cfg_path.write_text(json.dumps(future_cfg))
    loaded = m.load_semester_config()
    assert isinstance(loaded, dict)
    assert m.has_semester_ended(loaded) is False

    # write a past config and test has_semester_ended True
    past_cfg = {
        "semester_id": "past",
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    }
    cfg_path.write_text(json.dumps(past_cfg))
    loaded2 = m.load_semester_config()
    assert m.has_semester_ended(loaded2) is True
