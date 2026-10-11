import json
import tarfile
from io import BytesIO
from pathlib import Path

import pytest


def test_instances_root_creates_dir(tmp_path, monkeypatch):
    from kraken.core.instance import instances_root

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    root = instances_root()
    assert root == tmp_path / ".kraken" / "instances"
    assert root.is_dir()


def test_instance_home_valid(tmp_path, monkeypatch):
    from kraken.core.instance import instance_home

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    home = instance_home("my-inst")
    assert home == tmp_path / ".kraken" / "instances" / "my-inst"


def test_instance_home_invalid_names(tmp_path, monkeypatch):
    from kraken.core.instance import instance_home

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    for bad in ("bad name", "../etc", "", "a" * 64, "-leading"):
        with pytest.raises(ValueError):
            instance_home(bad)


def test_create_instance_with_label(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = create_instance("work", label="Work Instance")
    assert result["ok"] is True
    assert result["name"] == "work"
    meta = json.loads(
        (
            tmp_path / ".kraken" / "instances" / "work" / ".kraken" / "instance.json"
        ).read_text()
    )
    assert meta["label"] == "Work Instance"


def test_create_instance_without_label(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = create_instance("work")
    assert result["ok"] is True
    meta = json.loads(
        (
            tmp_path / ".kraken" / "instances" / "work" / ".kraken" / "instance.json"
        ).read_text()
    )
    assert meta["label"] == "work"


def test_list_instances_empty(tmp_path, monkeypatch):
    from kraken.core.instance import list_instances

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert list_instances() == []


def test_list_instances_with_meta(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, list_instances

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work", label="Work")
    rows = list_instances()
    assert len(rows) == 1
    assert rows[0]["name"] == "work"
    assert rows[0]["label"] == "Work"
    assert rows[0]["tentacles"] == 0


def test_list_instances_without_meta(tmp_path, monkeypatch):
    from kraken.core.instance import instance_home, list_instances

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    home = instance_home("bare")
    home.mkdir(parents=True)
    rows = list_instances()
    assert len(rows) == 1
    assert rows[0]["name"] == "bare"


def test_list_instances_skips_files(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, list_instances

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    (tmp_path / ".kraken" / "instances" / "stray.txt").write_text("x")
    rows = list_instances()
    assert len(rows) == 1


def test_list_instances_counts_tentacles(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, list_instances

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    tentacles = tmp_path / ".kraken" / "instances" / "work" / ".kraken" / "tentacles"
    tentacles.mkdir(parents=True, exist_ok=True)
    (tentacles / "geo").mkdir()
    (tentacles / "vault").mkdir()
    rows = list_instances()
    assert rows[0]["tentacles"] == 2


def test_export_bundle_no_kraken_dir(tmp_path, monkeypatch):
    from kraken.core.instance import export_bundle, instance_home

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    instance_home("empty").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        export_bundle("empty")


def test_export_bundle_success(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, export_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    kraken_dir = tmp_path / ".kraken" / "instances" / "work" / ".kraken"
    (kraken_dir / "config.yaml").write_text("version: 1\n")
    data = export_bundle("work")
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_export_bundle_skips_keys_logs_cache(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, export_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    kraken_dir = tmp_path / ".kraken" / "instances" / "work" / ".kraken"
    for skip in ("keys", "logs", "cache"):
        d = kraken_dir / skip
        d.mkdir(exist_ok=True)
        (d / "secret.txt").write_text("secret")
    data = export_bundle("work")
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as tar:
        names = tar.getnames()
    assert not any("keys" in n for n in names)
    assert not any("logs" in n for n in names)
    assert not any("cache" in n for n in names)


def test_export_bundle_skips_licenses_and_env(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, export_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    kraken_dir = tmp_path / ".kraken" / "instances" / "work" / ".kraken"
    (kraken_dir / "licenses.json").write_text("{}")
    (kraken_dir / ".env").write_text("SECRET=1")
    (kraken_dir / "config.yaml").write_text("version: 1\n")
    data = export_bundle("work")
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as tar:
        names = tar.getnames()
    assert not any("licenses.json" in n for n in names)
    assert not any(".env" in n for n in names)
    assert any("config.yaml" in n for n in names)


def test_export_bundle_includes_readme(tmp_path, monkeypatch):
    from kraken.core.instance import create_instance, export_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    create_instance("work")
    kraken_dir = tmp_path / ".kraken" / "instances" / "work" / ".kraken"
    (kraken_dir / "config.yaml").write_text("version: 1\n")
    data = export_bundle("work")
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as tar:
        names = tar.getnames()
        readme = tar.extractfile("work/README.txt").read().decode()
    assert "work" in readme
    assert "KRAKEN_HOME" in readme


def test_import_bundle_with_name(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        content = b"version: 1\n"
        info = tarfile.TarInfo("orig/.kraken/config.yaml")
        info.size = len(content)
        tar.addfile(info, BytesIO(content))
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    result = import_bundle(archive, name="renamed")
    assert result["ok"] is True
    assert result["name"] == "renamed"
    assert (
        tmp_path / ".kraken" / "instances" / "renamed" / ".kraken" / "config.yaml"
    ).exists()


def test_import_bundle_without_name(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        content = b"version: 1\n"
        info = tarfile.TarInfo("orig/.kraken/config.yaml")
        info.size = len(content)
        tar.addfile(info, BytesIO(content))
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    result = import_bundle(archive)
    assert result["ok"] is True
    assert result["name"] == "orig"


def test_import_bundle_extracts_keys_dir(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        content = b"secret"
        info = tarfile.TarInfo("orig/.kraken/keys/scopes.json")
        info.size = len(content)
        tar.addfile(info, BytesIO(content))
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    import_bundle(archive, name="clean")
    assert (
        tmp_path
        / ".kraken"
        / "instances"
        / "clean"
        / ".kraken"
        / "keys"
        / "scopes.json"
    ).exists()


def test_import_bundle_creates_dirs(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("orig/.kraken/tentacles")
        info.type = tarfile.DIRTYPE
        tar.addfile(info)
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    import_bundle(archive, name="withdirs")
    assert (
        tmp_path / ".kraken" / "instances" / "withdirs" / ".kraken" / "tentacles"
    ).is_dir()


def test_import_bundle_chmod_yaml(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        content = b"version: 1\n"
        info = tarfile.TarInfo("orig/.kraken/config.yaml")
        info.size = len(content)
        tar.addfile(info, BytesIO(content))
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    import_bundle(archive, name="chmodtest")
    target = (
        tmp_path / ".kraken" / "instances" / "chmodtest" / ".kraken" / "config.yaml"
    )
    if hasattr(target.stat(), "st_mode"):
        import stat

        assert stat.S_IMODE(target.stat().st_mode) & 0o777 == 0o600


def test_import_bundle_empty_archive(tmp_path, monkeypatch):
    from kraken.core.instance import import_bundle

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        pass
    archive = tmp_path / "bundle.tar.gz"
    archive.write_bytes(buf.getvalue())
    result = import_bundle(archive, name="empty")
    assert result["ok"] is True
    assert result["name"] == "empty"
