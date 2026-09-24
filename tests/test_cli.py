import logging

import pytest

from planta_filler import __version__
from planta_filler import cli as cli_mod
from planta_filler.core import RunOptions
from planta_filler.exceptions import BrowserError, LoginRequiredError


@pytest.fixture
def fake_run(monkeypatch):
    """Replace the browser and workflow with recorders."""
    calls = {}

    class DummyDriver:
        pass

    monkeypatch.setattr(cli_mod, "start_driver", lambda **kw: calls.setdefault("start", kw) or DummyDriver())
    monkeypatch.setattr(cli_mod, "end_driver", lambda d: calls.__setitem__("ended", True))
    monkeypatch.setattr(cli_mod, "run", lambda d, o: calls.__setitem__("options", o) or 0)
    return calls


def test_help_and_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_mod.main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli_mod.main(["--help"])
    assert "--export-reference" in capsys.readouterr().out


def test_man_page(capsys):
    assert cli_mod.main(["--man"]) == 0
    out = capsys.readouterr().out
    assert "NAME" in out and __version__ in out and "{" not in out


def test_full_fill_invocation(fake_run):
    code = cli_mod.main(
        [
            "--url",
            "https://example.com",
            "--strategy",
            "equal",
            "--week=0,-1",
            "--post-randomization",
            "0.2",
            "--weekdays",
            "0,2,4",
            "--exclude",
            "1, 3",
            "--close-delay",
            "0",
            "--delay",
            "0",
            "--headless",
            "--no-persistent",
        ]
    )
    assert code == 0
    options: RunOptions = fake_run["options"]
    assert options.week_specs == ["0", "-1"]
    assert options.weekdays == [0, 2, 4]
    assert options.exclude_indices == [1, 3]
    assert options.post_randomization == pytest.approx(0.2)
    assert options.interactive is False
    assert fake_run["start"] == {"headless": True, "use_persistent_profile": False}
    assert fake_run["ended"] is True


def test_reset_invocation(fake_run):
    assert cli_mod.main(["--url", "https://example.com", "--reset", "--weekdays", "1,3"]) == 0
    options = fake_run["options"]
    assert options.reset is True
    assert options.weekdays == [1, 3]
    assert fake_run["start"]["use_persistent_profile"] is True


def test_export_invocation(fake_run, tmp_path):
    out = tmp_path / "ref.csv"
    assert cli_mod.main(["--url", "https://example.com", "--export-reference", str(out)]) == 0
    assert fake_run["options"].export_reference == str(out)


def test_reference_file_is_validated_before_browser_starts(fake_run, tmp_path, capsys):
    ref = tmp_path / "ref.csv"
    ref.write_text(",Mo\n1,1\n")
    assert cli_mod.main(["--url", "https://x", "--strategy", "copy_reference", "--reference-file", str(ref)]) == 0
    assert fake_run["options"].reference_file == str(ref.resolve())

    fake_run.clear()
    code = cli_mod.main(["--url", "https://x", "--strategy", "copy_reference", "--reference-file", "nope.csv"])
    assert code == 2
    assert "start" not in fake_run
    assert "not found" in capsys.readouterr().out


def test_invalid_arguments_exit_2_without_browser(fake_run, capsys):
    assert cli_mod.main(["--url", "not-a-url", "--weekdays", "0,8", "--week", "abc"]) == 2
    out = capsys.readouterr().out
    assert "URL must start" in out and "weekday 8" in out and "Invalid week format" in out
    assert "start" not in fake_run

    assert cli_mod.main(["--url", "https://x", "--exclude", "a"]) == 2
    assert "--exclude" in capsys.readouterr().out


def test_invalid_strategy_is_rejected_by_argparse(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_mod.main(["--url", "https://x", "--strategy", "nope"])
    assert exc.value.code == 2


def test_browser_errors_map_to_exit_1(monkeypatch, capsys):
    def boom(**kw):
        raise BrowserError("no firefox")

    monkeypatch.setattr(cli_mod, "start_driver", boom)
    assert cli_mod.main(["--url", "https://x"]) == 1
    assert "no firefox" in capsys.readouterr().out


def test_run_errors_close_the_browser(monkeypatch, capsys):
    ended = []
    monkeypatch.setattr(cli_mod, "start_driver", lambda **kw: object())
    monkeypatch.setattr(cli_mod, "end_driver", lambda d: ended.append(d))

    def failing_run(driver, options):
        raise LoginRequiredError("please log in")

    monkeypatch.setattr(cli_mod, "run", failing_run)
    assert cli_mod.main(["--url", "https://x"]) == 1
    assert ended and "please log in" in capsys.readouterr().out

    def interrupted(driver, options):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli_mod, "run", interrupted)
    assert cli_mod.main(["--url", "https://x"]) == 130


def test_quiet_and_verbose_configure_logging(fake_run):
    cli_mod.main(["--url", "https://x", "--quiet"])
    assert logging.getLogger().level == logging.WARNING
    cli_mod.main(["--url", "https://x", "--verbose"])
    assert logging.getLogger().level == logging.DEBUG
