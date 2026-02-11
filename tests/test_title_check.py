import pytest

from planta_filler.core import _assert_planta_pulse_title


class D:
    def __init__(self, title):
        self.title = title


def test_assert_planta_pulse_title_accepts_valid_titles():
    _assert_planta_pulse_title(D("PLANTA Pulse - Home"))
    _assert_planta_pulse_title(D("planta pulse dashboard"))


def test_assert_planta_pulse_title_rejects_invalid_titles():
    with pytest.raises(Exception) as exc:
        _assert_planta_pulse_title(D("Some Other App"))
    assert "VPN" in str(exc.value) or "URL invalid" in str(exc.value)

    # Empty or missing title should also fail
    with pytest.raises(Exception):
        _assert_planta_pulse_title(D(""))
