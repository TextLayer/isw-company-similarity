import unittest

import numpy as np

from isw.core.services.similarity import RevenueSimilarityService


class TestRevenueSimilarityService(unittest.TestCase):
    """Tests for RevenueSimilarityService."""

    def setUp(self):
        self.service = RevenueSimilarityService(n_buckets=5)

    def test_default_n_buckets_is_20(self):
        """Default n_buckets should be 20."""
        service = RevenueSimilarityService()
        assert service.n_buckets == 20

    def test_compute_similarity_returns_correct_shape(self):
        """Similarity matrix should be n x n for n revenues."""
        revenues = np.array([1_000_000, 10_000_000, 100_000_000, 1_000_000_000])

        result = self.service.compute_similarity(revenues)

        assert result.similarity_matrix.shape == (4, 4)
        assert result.log_revenues.shape == (4,)
        assert result.valid_mask.shape == (4,)
        assert result.bucket_assignments.shape == (4,)

    def test_similarity_matrix_is_symmetric(self):
        """Revenue similarity should be symmetric."""
        revenues = np.array([1_000_000, 5_000_000, 10_000_000, 50_000_000])

        result = self.service.compute_similarity(revenues)

        np.testing.assert_array_almost_equal(
            result.similarity_matrix,
            result.similarity_matrix.T,
            decimal=10,
        )

    def test_self_similarity_is_one(self):
        """Diagonal should be 1 (self-similarity)."""
        revenues = np.array([1_000_000, 10_000_000, 100_000_000])

        result = self.service.compute_similarity(revenues)

        diagonal = np.diag(result.similarity_matrix)
        np.testing.assert_array_almost_equal(diagonal, np.ones(3), decimal=10)

    def test_similarity_values_between_zero_and_one(self):
        """All similarity values should be in [0, 1]."""
        revenues = np.array([100, 1_000_000, 1_000_000_000, 100_000_000_000])

        result = self.service.compute_similarity(revenues)

        assert np.all(result.similarity_matrix >= 0)
        assert np.all(result.similarity_matrix <= 1)

    def test_similar_revenues_have_high_similarity(self):
        """Companies with similar revenues should have higher similarity."""
        revenues = np.array([1_000_000, 2_000_000, 1_000_000_000])

        result = self.service.compute_similarity(revenues)

        sim_1m_2m = result.similarity_matrix[0, 1]
        sim_1m_1b = result.similarity_matrix[0, 2]

        assert sim_1m_2m > sim_1m_1b

    def test_handles_zero_revenue(self):
        """Should handle zero revenue using log1p."""
        revenues = np.array([0, 1_000_000, 10_000_000])

        result = self.service.compute_similarity(revenues)

        assert result.similarity_matrix.shape == (3, 3)
        assert not np.any(np.isnan(result.similarity_matrix))
        assert not np.any(np.isinf(result.similarity_matrix))

    def test_handles_missing_revenue_with_median(self):
        """Should replace missing revenues with median when strategy is 'median'."""
        service = RevenueSimilarityService(missing_value_strategy="median")
        revenues = np.array([1_000_000, np.nan, 10_000_000])

        result = service.compute_similarity(revenues)

        assert result.similarity_matrix.shape == (3, 3)
        assert not np.any(np.isnan(result.similarity_matrix))
        assert result.valid_mask[0]
        assert not result.valid_mask[1]
        assert result.valid_mask[2]

    def test_handles_missing_revenue_with_exclude(self):
        """Should set similarity to 0 for missing revenues when strategy is 'exclude'."""
        service = RevenueSimilarityService(missing_value_strategy="exclude")
        revenues = np.array([1_000_000, np.nan, 10_000_000])

        result = service.compute_similarity(revenues)

        assert result.similarity_matrix[1, 0] == 0
        assert result.similarity_matrix[0, 1] == 0
        assert result.similarity_matrix[1, 2] == 0
        assert result.similarity_matrix[0, 2] > 0

    def test_negative_revenue_treated_as_missing(self):
        """Negative revenues should be treated as missing."""
        service = RevenueSimilarityService(missing_value_strategy="exclude")
        revenues = np.array([1_000_000, -500, 10_000_000])

        result = service.compute_similarity(revenues)

        assert not result.valid_mask[1]

    def test_custom_scale_parameter(self):
        """Should use custom scale parameter when provided."""
        service = RevenueSimilarityService(scale=2.0)
        revenues = np.array([1_000_000, 10_000_000, 100_000_000])

        result = service.compute_similarity(revenues)

        assert result.scale == 2.0

    def test_raises_for_single_revenue(self):
        """Should raise error for single revenue value."""
        revenues = np.array([1_000_000])

        with self.assertRaises(ValueError) as ctx:
            self.service.compute_similarity(revenues)

        assert "at least 2" in str(ctx.exception).lower()

    def test_raises_for_all_missing(self):
        """Should raise error if all revenues are missing."""
        revenues = np.array([np.nan, np.nan, np.nan])

        with self.assertRaises(ValueError) as ctx:
            self.service.compute_similarity(revenues)

        assert "missing" in str(ctx.exception).lower() or "invalid" in str(ctx.exception).lower()

    def test_raises_for_invalid_missing_strategy(self):
        """Should raise error for invalid missing value strategy."""
        with self.assertRaises(ValueError):
            RevenueSimilarityService(missing_value_strategy="invalid")

    def test_raises_for_invalid_n_buckets(self):
        """Should raise error for n_buckets < 1."""
        with self.assertRaises(ValueError):
            RevenueSimilarityService(n_buckets=0)


class TestDynamicBuckets(unittest.TestCase):
    """Tests for dynamic revenue bucketing."""

    def setUp(self):
        self.service = RevenueSimilarityService(n_buckets=5)

    def test_buckets_created_from_data(self):
        """Buckets should be created based on actual data range."""
        revenues = np.array([1_000, 10_000, 100_000, 1_000_000, 10_000_000])

        result = self.service.compute_similarity(revenues)

        assert result.buckets.n_buckets == 5
        assert result.buckets.min_revenue == 1_000
        assert result.buckets.max_revenue == 10_000_000
        assert len(result.buckets.boundaries) == 6  # n+1 boundaries

    def test_bucket_assignments_valid(self):
        """Each company should be assigned to a valid bucket."""
        revenues = np.array([1_000, 10_000, 100_000, 1_000_000, 10_000_000])

        result = self.service.compute_similarity(revenues)

        assert np.all(result.bucket_assignments >= 0)
        assert np.all(result.bucket_assignments < result.buckets.n_buckets)

    def test_custom_n_buckets(self):
        """Should respect custom n_buckets parameter."""
        service = RevenueSimilarityService(n_buckets=3)
        revenues = np.array([1_000, 10_000, 100_000, 1_000_000])

        result = service.compute_similarity(revenues)

        assert result.buckets.n_buckets == 3
        assert len(result.buckets.boundaries) == 4

    def test_bucket_index_for_invalid_revenue(self):
        """Invalid revenue should return -1 bucket index."""
        revenues = np.array([1_000_000, 10_000_000])
        result = self.service.compute_similarity(revenues)

        assert result.buckets.get_bucket_index(-100) == -1
        assert result.buckets.get_bucket_index(np.nan) == -1

    def test_vectorized_bucket_indices(self):
        """Vectorized bucket assignment should match individual calls."""
        revenues = np.array([1_000, 10_000, 100_000, 1_000_000])
        result = self.service.compute_similarity(revenues)

        # Compare vectorized vs individual
        individual = [result.buckets.get_bucket_index(r) for r in revenues]
        vectorized = result.buckets.get_bucket_indices(revenues)

        np.testing.assert_array_equal(vectorized, individual)

    def test_vectorized_handles_invalid(self):
        """Vectorized assignment should handle invalid values."""
        revenues = np.array([1_000_000, 10_000_000])
        result = self.service.compute_similarity(revenues)

        test_revenues = np.array([1_000_000, -100, np.nan, 5_000_000])
        indices = result.buckets.get_bucket_indices(test_revenues)

        assert indices[0] >= 0  # Valid
        assert indices[1] == -1  # Negative
        assert indices[2] == -1  # NaN
        assert indices[3] >= 0  # Valid


class TestGetTopSimilar(unittest.TestCase):
    """Tests for get_top_similar method."""

    def setUp(self):
        self.service = RevenueSimilarityService(n_buckets=5)

    def test_returns_correct_number_of_results(self):
        """Should return k results."""
        revenues = np.array([1_000_000, 2_000_000, 10_000_000, 100_000_000])
        result = self.service.compute_similarity(revenues)

        top = self.service.get_top_similar(result.similarity_matrix, index=0, k=2)

        assert len(top) == 2

    def test_results_sorted_by_similarity_descending(self):
        """Results should be sorted by similarity in descending order."""
        revenues = np.array([1_000_000, 2_000_000, 10_000_000, 100_000_000])
        result = self.service.compute_similarity(revenues)

        top = self.service.get_top_similar(result.similarity_matrix, index=0, k=3)

        similarities = [r[1] for r in top]
        assert similarities == sorted(similarities, reverse=True)

    def test_excludes_self_by_default(self):
        """Should exclude the item itself from results by default."""
        revenues = np.array([1_000_000, 2_000_000, 10_000_000])
        result = self.service.compute_similarity(revenues)

        top = self.service.get_top_similar(result.similarity_matrix, index=0, k=3)

        indices = [r[0] for r in top]
        assert 0 not in indices

    def test_includes_self_when_specified(self):
        """Should include self when exclude_self=False."""
        revenues = np.array([1_000_000, 2_000_000, 10_000_000])
        result = self.service.compute_similarity(revenues)

        top = self.service.get_top_similar(result.similarity_matrix, index=0, k=3, exclude_self=False)

        indices = [r[0] for r in top]
        assert 0 in indices
        # Self should be first (highest similarity = 1.0)
        assert top[0][0] == 0
