import pytest
import sys
from pathlib import Path

sys.path.append((Path(__file__).resolve().parents[1] / "src/key_craftsman").as_posix())
from key_craftsman import (
    excluder_chart,
    generate_fernet_keys,
    KeyCraftsman,
    KeyException,
)


@pytest.fixture(params=[excluder_chart()])
def test_excluder_chart_method(request):
    return request.param


def test_excluder_chart(test_excluder_chart_method):
    e_chart = test_excluder_chart_method
    assert isinstance(e_chart, dict) is True
    assert len(e_chart) == 29


def test_exclude_chars_param(test_excluder_chart_method):
    e_chart = test_excluder_chart_method

    def checker(k, data):
        assert (
            KeyCraftsman._compiler(
                KeyCraftsman.char_excluder(k), data, escape_default=False
            )
            is None
        )

    for t in e_chart:
        kcraft = KeyCraftsman(exclude_chars=t)
        key, keys = kcraft.key, kcraft.keys
        checker(t, key)
        checker(t, keys)
    kcraft.export_key()


@pytest.fixture(params=[generate_fernet_keys])
def test_generate_fernet_keys_method(request):
    return request.param


def test_generate_fernet_keys(test_generate_fernet_keys_method):
    fernet_func = test_generate_fernet_keys_method
    is_instance = KeyCraftsman._obj_instance
    fernet_key = fernet_func()
    assert is_instance(fernet_key, bytes)
    fernet_keys = fernet_func(num_of_keys=2)
    assert is_instance(fernet_keys, dict)
    assert len(fernet_keys) == 2
    assert all((is_instance(v, bytes) for v in fernet_keys.values()))

    with pytest.raises(KeyException):
        fernet_func(num_of_keys=sys.maxsize)
