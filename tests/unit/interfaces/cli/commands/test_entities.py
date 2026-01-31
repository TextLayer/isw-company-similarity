import unittest

from click.testing import CliRunner

from isw.interfaces.cli.commands.entities import entities


class TestCollectCommand(unittest.TestCase):
    def test_collect_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["collect", "--help"])
        assert result.exit_code == 0
        assert "Collect entities" in result.output

    def test_collect_limit_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["collect", "--help"])
        assert "--limit" in result.output

    def test_collect_source_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["collect", "--help"])
        assert "--source" in result.output


class TestEnrichCommand(unittest.TestCase):
    def test_enrich_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert result.exit_code == 0

    def test_limit_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--limit" in result.output

    def test_jurisdiction_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--jurisdiction" in result.output

    def test_skip_embeddings_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--skip-embeddings" in result.output

    def test_no_llm_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--no-llm" in result.output

    def test_force_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["enrich", "--help"])
        assert "--force" in result.output


class TestNormalizeRevenueCommand(unittest.TestCase):
    def test_normalize_revenue_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["normalize-revenue", "--help"])
        assert result.exit_code == 0

    def test_n_buckets_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["normalize-revenue", "--help"])
        assert "--n-buckets" in result.output

    def test_force_option(self):
        runner = CliRunner()
        result = runner.invoke(entities, ["normalize-revenue", "--help"])
        assert "--force" in result.output
