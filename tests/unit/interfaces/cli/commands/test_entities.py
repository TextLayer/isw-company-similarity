import unittest

from click.testing import CliRunner

from isw.interfaces.cli.commands.entities import EnrichedEntity, entities


class TestEnrichedEntity(unittest.TestCase):
    def test_to_dict_basic(self):
        entity = EnrichedEntity(
            name="Test Company",
            identifier="0001234567",
            jurisdiction="US",
            identifier_type="CIK",
        )
        result = entity.to_dict()

        assert result["name"] == "Test Company"
        assert result["identifier"] == "0001234567"
        assert result["jurisdiction"] == "US"
        assert result["identifier_type"] == "CIK"
        assert "business_description" not in result
        assert "embedding" not in result
        assert "enrichment_error" not in result

    def test_to_dict_with_description(self):
        entity = EnrichedEntity(
            name="Test Company",
            identifier="0001234567",
            jurisdiction="US",
            identifier_type="CIK",
            business_description="Test description",
        )
        result = entity.to_dict()

        assert result["business_description"] == "Test description"

    def test_to_dict_with_embedding(self):
        entity = EnrichedEntity(
            name="Test Company",
            identifier="0001234567",
            jurisdiction="US",
            identifier_type="CIK",
            embedding=[0.1, 0.2, 0.3],
        )
        result = entity.to_dict()

        assert result["embedding"] == [0.1, 0.2, 0.3]

    def test_to_dict_with_error(self):
        entity = EnrichedEntity(
            name="Test Company",
            identifier="0001234567",
            jurisdiction="US",
            identifier_type="CIK",
            enrichment_error="Failed to fetch",
        )
        result = entity.to_dict()

        assert result["enrichment_error"] == "Failed to fetch"


class TestEnrichCommand(unittest.TestCase):
    def test_enrich_command_exists(self):
        """Verify the enrich command is registered."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert result.exit_code == 0
        assert "Enrich entities with business descriptions" in result.output

    def test_enrich_requires_input_and_output(self):
        """Verify enrich command requires input and output options."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich"])
        assert result.exit_code != 0
        assert "Missing option" in result.output


class TestCollectCommand(unittest.TestCase):
    def test_collect_command_exists(self):
        """Verify the collect command is registered."""
        runner = CliRunner()
        result = runner.invoke(entities, ["collect", "--help"])
        assert result.exit_code == 0
        assert "Collect entity master list" in result.output

    def test_collect_dry_run(self):
        """Verify dry run mode works."""
        runner = CliRunner()
        result = runner.invoke(entities, ["collect", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.output
