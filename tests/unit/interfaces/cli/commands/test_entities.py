import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from isw.interfaces.cli.commands.entities import (
    EnrichedEntity,
    EnrichmentCheckpoint,
    entities,
)


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


class TestEnrichOptions(unittest.TestCase):
    """Test enrich command options."""

    def test_limit_option_documented(self):
        """Verify --limit option exists and is documented."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--limit" in result.output
        assert "Limit the number of entities to process" in result.output

    def test_resume_from_option_documented(self):
        """Verify --resume-from option exists and is documented."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--resume-from" in result.output
        assert "Resume processing from this entity index" in result.output

    def test_delay_option_documented(self):
        """Verify --delay option exists and is documented."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--delay" in result.output

    def test_skip_embeddings_option_documented(self):
        """Verify --skip-embeddings option exists and is documented."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--skip-embeddings" in result.output


class TestEnrichmentCheckpoint(unittest.TestCase):
    """Tests for EnrichmentCheckpoint class."""

    def test_to_dict_and_from_dict_roundtrip(self):
        """Checkpoint should serialize and deserialize correctly."""
        checkpoint = EnrichmentCheckpoint(
            processed_identifiers={"id1", "id2", "id3"},
            enriched_entities=[{"name": "Company 1"}, {"name": "Company 2"}],
            started_at="2024-01-01T00:00:00",
            last_updated_at="2024-01-01T01:00:00",
            input_file="entities.json",
            total_entities=100,
        )

        data = checkpoint.to_dict()
        restored = EnrichmentCheckpoint.from_dict(data)

        assert restored.processed_identifiers == checkpoint.processed_identifiers
        assert restored.enriched_entities == checkpoint.enriched_entities
        assert restored.started_at == checkpoint.started_at
        assert restored.input_file == checkpoint.input_file
        assert restored.total_entities == checkpoint.total_entities

    def test_save_and_load(self):
        """Checkpoint should save and load from file correctly."""
        checkpoint = EnrichmentCheckpoint(
            processed_identifiers={"id1", "id2"},
            enriched_entities=[{"name": "Test"}],
            started_at="2024-01-01T00:00:00",
            input_file="test.json",
            total_entities=50,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checkpoint.json"

            checkpoint.save(path)
            assert path.exists()

            loaded = EnrichmentCheckpoint.load(path)
            assert loaded is not None
            assert loaded.processed_identifiers == checkpoint.processed_identifiers
            assert loaded.enriched_entities == checkpoint.enriched_entities

    def test_load_nonexistent_returns_none(self):
        """Loading nonexistent checkpoint should return None."""
        result = EnrichmentCheckpoint.load(Path("/nonexistent/path/checkpoint.json"))
        assert result is None

    def test_load_corrupted_returns_none(self):
        """Loading corrupted checkpoint should return None with warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "corrupted.json"
            path.write_text("{ invalid json }")

            result = EnrichmentCheckpoint.load(path)
            assert result is None

    def test_save_creates_parent_directories(self):
        """Save should create parent directories if they don't exist."""
        checkpoint = EnrichmentCheckpoint()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "checkpoint.json"

            checkpoint.save(path)
            assert path.exists()


class TestCheckpointOptions(unittest.TestCase):
    """Test checkpoint-related CLI options."""

    def test_checkpoint_option_documented(self):
        """Verify --checkpoint option exists and is documented."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--checkpoint" in result.output
        assert "Checkpoint file for resumable processing" in result.output

    def test_checkpoint_interval_option_documented(self):
        """Verify --checkpoint-interval option exists."""
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--checkpoint-interval" in result.output


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
