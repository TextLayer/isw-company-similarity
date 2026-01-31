"""Unit tests for entity identifier validation edge cases.

These tests protect against common validation bugs and edge cases
that are easy to get wrong without proper testing.
"""

import pytest

from isw.core.services.entities import CIK, LEI, is_cik, is_lei, parse_identifier


class TestCIKValidation:
    """CIK validation edge cases."""

    def test_valid_short_cik(self):
        """Short CIKs should be zero-padded to 10 digits."""
        cik = CIK("320193")
        assert cik.value == "0000320193"

    def test_valid_full_length_cik(self):
        """Full 10-digit CIKs should be preserved."""
        cik = CIK("0000320193")
        assert cik.value == "0000320193"

    def test_valid_cik_with_leading_zeros(self):
        """Leading zeros should be normalized correctly."""
        cik = CIK("00000320193")  # 11 digits with extra leading zero
        assert cik.value == "0000320193"

    def test_valid_cik_all_zeros(self):
        """All zeros is technically valid (though unlikely in practice)."""
        cik = CIK("0000000000")
        assert cik.value == "0000000000"

    def test_invalid_cik_non_numeric(self):
        """Non-numeric strings should be rejected."""
        with pytest.raises(ValueError, match="Invalid CIK"):
            CIK("abc123")

    def test_invalid_cik_empty(self):
        """Empty strings should be rejected."""
        with pytest.raises(ValueError, match="Invalid CIK"):
            CIK("")

    def test_invalid_cik_too_long(self):
        """CIKs longer than 10 digits (after stripping zeros) should be rejected."""
        with pytest.raises(ValueError, match="Invalid CIK"):
            CIK("12345678901")  # 11 non-zero digits

    def test_cik_equality(self):
        """CIKs with same normalized value should be equal."""
        assert CIK("320193") == CIK("0000320193")

    def test_cik_hash(self):
        """Equal CIKs should have same hash for use in sets/dicts."""
        cik1 = CIK("320193")
        cik2 = CIK("0000320193")
        assert hash(cik1) == hash(cik2)
        assert {cik1} == {cik2}


class TestLEIValidation:
    """LEI validation edge cases."""

    def test_valid_lei(self):
        """Standard 20-character LEI should be accepted."""
        lei = LEI("529900T8BM49AURSDO55")
        assert lei.value == "529900T8BM49AURSDO55"

    def test_valid_lei_lowercase(self):
        """Lowercase LEIs should be normalized to uppercase."""
        lei = LEI("529900t8bm49aursdo55")
        assert lei.value == "529900T8BM49AURSDO55"

    def test_valid_lei_mixed_case(self):
        """Mixed case LEIs should be normalized."""
        lei = LEI("529900T8Bm49AuRsDo55")
        assert lei.value == "529900T8BM49AURSDO55"

    def test_invalid_lei_too_short(self):
        """LEIs shorter than 20 characters should be rejected."""
        with pytest.raises(ValueError, match="Invalid LEI"):
            LEI("529900T8BM49AURS")

    def test_invalid_lei_too_long(self):
        """LEIs longer than 20 characters should be rejected."""
        with pytest.raises(ValueError, match="Invalid LEI"):
            LEI("529900T8BM49AURSDO55X")

    def test_invalid_lei_special_characters(self):
        """LEIs with special characters should be rejected."""
        with pytest.raises(ValueError, match="Invalid LEI"):
            LEI("529900T8BM49AURS-O55")

    def test_invalid_lei_empty(self):
        """Empty strings should be rejected."""
        with pytest.raises(ValueError, match="Invalid LEI"):
            LEI("")

    def test_lei_equality(self):
        """LEIs with same value should be equal."""
        assert LEI("529900T8BM49AURSDO55") == LEI("529900t8bm49aursdo55")

    def test_lei_hash(self):
        """Equal LEIs should have same hash."""
        lei1 = LEI("529900T8BM49AURSDO55")
        lei2 = LEI("529900t8bm49aursdo55")
        assert hash(lei1) == hash(lei2)


class TestParseIdentifier:
    """Tests for automatic identifier type detection."""

    def test_parse_numeric_as_cik(self):
        """Numeric strings should be parsed as CIK."""
        result = parse_identifier("320193")
        assert isinstance(result, CIK)

    def test_parse_alphanumeric_20_as_lei(self):
        """20-character alphanumeric strings should be parsed as LEI."""
        result = parse_identifier("529900T8BM49AURSDO55")
        assert isinstance(result, LEI)

    def test_parse_unknown_format_raises(self):
        """Unknown formats should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown identifier"):
            parse_identifier("not-a-valid-id")

    def test_parse_ambiguous_numeric_prefers_cik(self):
        """20-digit numeric could be LEI, but we prefer CIK for numeric."""
        # This is a tricky edge case - a 20-digit all-numeric string
        # It's technically a valid LEI format but also looks like a very long CIK
        # CIK check happens first, but a 20-digit numeric is too long for CIK
        # So it should be parsed as LEI
        result = parse_identifier("12345678901234567890")
        assert isinstance(result, LEI)


class TestConvenienceFunctions:
    """Tests for is_cik and is_lei helper functions."""

    def test_is_cik_true(self):
        """is_cik should return True for valid CIKs."""
        assert is_cik("320193") is True
        assert is_cik("0000320193") is True

    def test_is_cik_false(self):
        """is_cik should return False for invalid CIKs."""
        assert is_cik("529900T8BM49AURSDO55") is False
        assert is_cik("") is False
        assert is_cik("abc") is False

    def test_is_lei_true(self):
        """is_lei should return True for valid LEIs."""
        assert is_lei("529900T8BM49AURSDO55") is True
        assert is_lei("213800H2PQMIF3OVZY47") is True

    def test_is_lei_false(self):
        """is_lei should return False for invalid LEIs."""
        assert is_lei("320193") is False
        assert is_lei("") is False
        assert is_lei("too-short") is False
