import pytest
from ..src.key_craftsman import (
    excluder_chart,
    generate_secure_keys,
    KeyCraftsman,
    KeyException,
    _get_method,
)


MAX_C = KeyCraftsman._MAX_CAPACITY
ALL_CHARS = KeyCraftsman._ALL_CHARS
unpack = KeyCraftsman.unpack
validate_ktuple = KeyCraftsman._validate_ktuple


def kc(**kwargs):
    attr, status = (kwargs.pop(i, j) for i, j in (("attr", "key"), ("status", False)))
    return _get_method(KeyCraftsman(**kwargs), attr=attr, status=status)


@pytest.fixture(
    name="class_params",
    params=[
        (
            {"key_length": None},
            {"key_length": MAX_C},
            {"keyfile_name": 7},
            {"num_of_keys": MAX_C},
            {"num_of_words": MAX_C, "use_words": True},
            {"sep": "large-sep"},
            {"exclude_chars": ALL_CHARS},
        )
    ],
)
def test_class_params(request):
    return request.param


def test_class_params_fails(class_params):
    for params in class_params:
        with pytest.raises(KeyException):
            if "keyfile_name" in params:
                kc(**params, attr="export_key")
            elif "num_of_keys" in params:
                kc(**params, attr="keys")
            else:
                kc(**params)


@pytest.fixture(
    name="combo_params",
    params=[
        (
            {
                "encoded": True,
                "urlsafe_encoded": True,
            },
            {
                "exclude_chars": "punct",
                "include_all_chars": True,
            },
        )
    ],
)
def test_combo_params(request):
    return request.param


def test_combo_params_fails(combo_params):
    for params in combo_params:
        with pytest.raises(KeyException):
            kc(**params)


@pytest.fixture(params=[excluder_chart(format_type="dict")], name="exclude_options")
def test_excluder_chart_method(request):
    return request.param


def test_excluder_chart(exclude_options):
    assert isinstance(exclude_options, dict) is True
    assert len(exclude_options) == 31


def test_exclude_chars_param(exclude_options):
    e_chart = exclude_options

    def checker(k, data):
        assert (
            KeyCraftsman._compiler(
                KeyCraftsman.char_excluder(k), data, escape_default=False
            )
            is None
        )

    for idx, k in enumerate(e_chart, start=1):
        # Checks based on excluder option key
        kcraft = KeyCraftsman(exclude_chars=k)
        key, keys = kcraft.key, kcraft.keys
        checker(k, key)
        checker(k, unpack(keys))

        # Checks based on exlcuder option index
        kcraft_idx = KeyCraftsman(exclude_chars=idx)
        key, keys = kcraft_idx.key, kcraft_idx.keys
        checker(k, key)
        checker(k, unpack(keys))


@pytest.fixture(params=[generate_secure_keys], name="securekeys")
def test_generate_securekeys_method(request):
    return request.param


def test_generate_securekeys(securekeys):
    keys = securekeys()
    secure_keys = unpack(keys)
    assert validate_ktuple(keys)
    with pytest.raises(KeyException):
        for v in secure_keys:
            KeyCraftsman._obj_instance(v, str)
    assert all((isinstance(v, bytes) for v in secure_keys))
    assert len(secure_keys) == 2
    secure_key = securekeys(num_of_keys=None)
    assert isinstance(secure_key, bytes)

    with pytest.raises(KeyException):
        securekeys(num_of_keys=MAX_C)


@pytest.fixture(params=[({"unique_chars": True})], name="unique_set")
def test_unique_keys_param(request):
    return request.param


def test_unique_keys_set(unique_set):
    def set_checker(data):
        assert KeyCraftsman.unique_test(data, test_only=True) is True

    key = kc(**unique_set)
    assert isinstance(key, str)
    set_checker(key)

    keys = kc(**unique_set, status=True)
    assert validate_ktuple(keys)
    for idx, (k, v) in enumerate(keys._asdict().items(), start=1):
        assert k == f"key{idx}"
        set_checker(v)


@pytest.fixture(params=[({"num_of_keys": (nm := 3)})], name="class_iter")
def test_class_iter_obj(request):
    return request.param


def test_class_iter(class_iter):
    kc_keys = KeyCraftsman(**class_iter)
    with pytest.raises(StopIteration):
        for idx in range(nm + 1):
            assert idx == kc_keys.index
            next(kc_keys)
