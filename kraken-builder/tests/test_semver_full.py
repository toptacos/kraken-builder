import pytest

from kraken.core.semver import _match_token, cmp_version, parse_version, satisfies


def test_parse_version_full():
    assert parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_empty():
    assert parse_version("") == (0, 0, 0)


def test_parse_version_none():
    assert parse_version(None) == (0, 0, 0)


def test_parse_version_partial():
    assert parse_version("1.2") == (1, 2, 0)
    assert parse_version("1") == (1, 0, 0)


def test_parse_version_extra_parts():
    assert parse_version("1.2.3.4") == (1, 2, 3)


def test_parse_version_with_v_prefix():
    assert parse_version("v1.2.3") == (1, 2, 3)


def test_parse_version_with_build_metadata():
    assert parse_version("1.2.3+build456") == (1, 2, 3)


def test_parse_version_with_prerelease():
    assert parse_version("1.2.3-rc1") == (1, 2, 3)


def test_parse_version_whitespace():
    assert parse_version("  1.2.3  ") == (1, 2, 3)


def test_cmp_version_equal():
    assert cmp_version("1.2.3", "1.2.3") == 0


def test_cmp_version_greater():
    assert cmp_version("1.2.3", "1.2.2") == 1
    assert cmp_version("2.0.0", "1.9.9") == 1


def test_cmp_version_less():
    assert cmp_version("1.2.3", "1.2.4") == -1
    assert cmp_version("0.9.9", "1.0.0") == -1


def test_match_token_empty():
    assert _match_token("1.0.0", "") is True


def test_match_token_wildcard():
    assert _match_token("1.0.0", "*") is True
    assert _match_token("1.0.0", "any") is True


def test_match_token_optional():
    assert _match_token("1.0.0", "optional") is True


def test_match_token_caret_within():
    assert _match_token("1.5.0", "^1.2.0") is True


def test_match_token_caret_below():
    assert _match_token("1.1.0", "^1.2.0") is False


def test_match_token_caret_above():
    assert _match_token("2.0.0", "^1.2.0") is False


def test_match_token_tilde_within():
    assert _match_token("1.2.5", "~1.2.0") is True


def test_match_token_tilde_below():
    assert _match_token("1.1.0", "~1.2.0") is False


def test_match_token_tilde_above():
    assert _match_token("1.3.0", "~1.2.0") is False


def test_match_token_gte():
    assert _match_token("1.2.0", ">=1.2.0") is True
    assert _match_token("1.3.0", ">=1.2.0") is True
    assert _match_token("1.1.0", ">=1.2.0") is False


def test_match_token_lte():
    assert _match_token("1.2.0", "<=1.2.0") is True
    assert _match_token("1.1.0", "<=1.2.0") is True
    assert _match_token("1.3.0", "<=1.2.0") is False


def test_match_token_gt():
    assert _match_token("1.3.0", ">1.2.0") is True
    assert _match_token("1.2.0", ">1.2.0") is False


def test_match_token_lt():
    assert _match_token("1.1.0", "<1.2.0") is True
    assert _match_token("1.2.0", "<1.2.0") is False


def test_match_token_eq():
    assert _match_token("1.2.0", "==1.2.0") is True
    assert _match_token("1.2.1", "==1.2.0") is False


def test_match_token_single_eq():
    assert _match_token("1.2.0", "=1.2.0") is True
    assert _match_token("1.2.1", "=1.2.0") is False


def test_match_token_plain_version():
    assert _match_token("1.2.3", "1.2.3") is True
    assert _match_token("1.2.4", "1.2.3") is False


def test_satisfies_none_spec():
    assert satisfies("1.0.0", None) is True


def test_satisfies_empty_spec():
    assert satisfies("1.0.0", "") is True


def test_satisfies_wildcard_spec():
    assert satisfies("1.0.0", "*") is True
    assert satisfies("1.0.0", "any") is True
    assert satisfies("1.0.0", "optional") is True


def test_satisfies_whitespace_spec():
    assert satisfies("1.0.0", "  ") is True


def test_satisfies_single_token():
    assert satisfies("1.5.0", "^1.2.0") is True
    assert satisfies("2.0.0", "^1.2.0") is False


def test_satisfies_multiple_tokens():
    assert satisfies("1.5.0", ">=1.0.0 <2.0.0") is True
    assert satisfies("2.0.0", ">=1.0.0 <2.0.0") is False


def test_satisfies_one_token_fails():
    assert satisfies("0.5.0", ">=1.0.0 <2.0.0") is False
