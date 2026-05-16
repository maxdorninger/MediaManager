import pytest

from media_manager.torrent.utils import (
    extract_external_id_from_string,
    remove_special_characters,
    remove_special_chars_and_parentheses,
)


class TestRemoveSpecialCharacters:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("normal title", "normal title"),
            ('weird:"/\\|?*name', "weirdname"),
            ("Show <2024>", "Show 2024"),
            ("  spaced.  ", "spaced"),
            ("....leading.dots", "leading.dots"),
        ],
    )
    def test_strips_invalid_chars_and_trims(self, raw: str, expected: str) -> None:
        assert remove_special_characters(raw) == expected


class TestRemoveSpecialCharsAndParentheses:
    def test_strips_year_in_parens(self) -> None:
        assert remove_special_chars_and_parentheses("The Show (2024)") == "The Show"

    def test_strips_square_and_curly_bracket_groups(self) -> None:
        assert remove_special_chars_and_parentheses("Show [1080p] {x265}") == "Show"

    def test_collapses_whitespace(self) -> None:
        assert (
            remove_special_chars_and_parentheses("Show   Name    (2024)") == "Show Name"
        )

    def test_keeps_non_year_parentheses(self) -> None:
        # The year-in-parens rule only matches exactly 4 digits; other
        # parenthesized content is left intact (parens aren't in the
        # special-character set).
        assert remove_special_chars_and_parentheses("Show (US)") == "Show (US)"


class TestExtractExternalIdFromString:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Some Show tmdb-12345", ("tmdb", 12345)),
            ("Movie {tvdbid-67890}", ("tvdb", 67890)),
            ("Folder name TMDB_42 here", ("tmdb", 42)),
            ("show.tvdb-99", ("tvdb", 99)),
        ],
    )
    def test_finds_known_providers(self, raw: str, expected: tuple[str, int]) -> None:
        assert extract_external_id_from_string(raw) == expected

    def test_returns_none_when_absent(self) -> None:
        assert extract_external_id_from_string("plain folder name") == (None, None)

    def test_returns_none_for_unknown_provider(self) -> None:
        assert extract_external_id_from_string("imdb-12345") == (None, None)
