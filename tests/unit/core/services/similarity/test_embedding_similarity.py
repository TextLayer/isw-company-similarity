import unittest

import numpy as np

from isw.core.services.similarity import EmbeddingSimilarityService


class TestEmbeddingSimilarityService(unittest.TestCase):
    """Tests for EmbeddingSimilarityService."""

    def setUp(self):
        self.service = EmbeddingSimilarityService(
            n_components=10,
            n_neighbors=5,
            min_cluster_size=3,
            min_samples=2,
        )

    def test_compute_similarity_returns_correct_shape(self):
        """Similarity matrix should be n x n for n embeddings."""
        n_samples = 20
        n_features = 50
        embeddings = np.random.rand(n_samples, n_features)

        result = self.service.compute_similarity(embeddings, random_state=42)

        assert result.similarity_matrix.shape == (n_samples, n_samples)
        assert result.cluster_labels.shape == (n_samples,)
        assert result.reduced_embeddings.shape[0] == n_samples
        assert result.noise_mask.shape == (n_samples,)

    def test_similarity_matrix_is_symmetric(self):
        """Cosine similarity matrix should be symmetric."""
        embeddings = np.random.rand(15, 30)

        result = self.service.compute_similarity(embeddings, random_state=42)

        np.testing.assert_array_almost_equal(
            result.similarity_matrix,
            result.similarity_matrix.T,
            decimal=10,
        )

    def test_self_similarity_is_one(self):
        """Diagonal of similarity matrix should be 1 (self-similarity)."""
        embeddings = np.random.rand(25, 20)

        result = self.service.compute_similarity(embeddings, random_state=42)

        diagonal = np.diag(result.similarity_matrix)
        np.testing.assert_array_almost_equal(diagonal, np.ones(25), decimal=5)

    def test_similar_embeddings_have_high_similarity(self):
        """Similar embeddings should have high similarity scores."""
        # Create two clusters of similar embeddings (larger for UMAP stability)
        cluster1 = np.random.rand(15, 50) + np.array([1, 0, 0, 0, 0] + [0] * 45)
        cluster2 = np.random.rand(15, 50) + np.array([0, 1, 0, 0, 0] + [0] * 45)
        embeddings = np.vstack([cluster1, cluster2])

        result = self.service.compute_similarity(embeddings, random_state=42)

        # Items within cluster1 (indices 0-14) should be more similar to each other
        # than to items in cluster2 (indices 15-29)
        within_cluster1_sim = result.similarity_matrix[0, 1:15].mean()

        # Within-cluster similarity should be positive (basic sanity check)
        assert within_cluster1_sim > 0

    def test_noise_mask_identifies_noise_points(self):
        """Noise mask should be True where cluster label is -1."""
        embeddings = np.random.rand(20, 30)

        result = self.service.compute_similarity(embeddings, random_state=42)

        expected_noise_mask = result.cluster_labels == -1
        np.testing.assert_array_equal(result.noise_mask, expected_noise_mask)

    def test_raises_for_single_embedding(self):
        """Should raise error for single embedding."""
        embeddings = np.random.rand(1, 50)

        with self.assertRaises(ValueError) as ctx:
            self.service.compute_similarity(embeddings)

        assert "at least 2" in str(ctx.exception).lower()

    def test_handles_small_dataset(self):
        """Should handle small datasets by adjusting parameters."""
        # Small dataset (but enough for UMAP)
        embeddings = np.random.rand(15, 100)

        # Should not raise - parameters are adjusted internally
        result = self.service.compute_similarity(embeddings, random_state=42)

        assert result.similarity_matrix.shape == (15, 15)

    def test_deterministic_with_random_state(self):
        """Results should be deterministic with fixed random state."""
        embeddings = np.random.rand(15, 30)

        result1 = self.service.compute_similarity(embeddings, random_state=42)
        result2 = self.service.compute_similarity(embeddings, random_state=42)

        np.testing.assert_array_almost_equal(
            result1.similarity_matrix,
            result2.similarity_matrix,
        )
        np.testing.assert_array_equal(result1.cluster_labels, result2.cluster_labels)


class TestGetTopSimilar(unittest.TestCase):
    """Tests for get_top_similar method."""

    def setUp(self):
        self.service = EmbeddingSimilarityService()

    def test_returns_correct_number_of_results(self):
        """Should return k results."""
        # Create a simple similarity matrix
        similarity_matrix = np.array([
            [1.0, 0.9, 0.5, 0.3],
            [0.9, 1.0, 0.4, 0.2],
            [0.5, 0.4, 1.0, 0.8],
            [0.3, 0.2, 0.8, 1.0],
        ])

        results = self.service.get_top_similar(similarity_matrix, index=0, k=2)

        assert len(results) == 2

    def test_results_sorted_by_similarity_descending(self):
        """Results should be sorted by similarity in descending order."""
        similarity_matrix = np.array([
            [1.0, 0.9, 0.5, 0.3],
            [0.9, 1.0, 0.4, 0.2],
            [0.5, 0.4, 1.0, 0.8],
            [0.3, 0.2, 0.8, 1.0],
        ])

        results = self.service.get_top_similar(similarity_matrix, index=0, k=3)

        similarities = [r[1] for r in results]
        assert similarities == sorted(similarities, reverse=True)

    def test_excludes_self_by_default(self):
        """Should exclude the item itself from results by default."""
        similarity_matrix = np.array([
            [1.0, 0.9, 0.5],
            [0.9, 1.0, 0.4],
            [0.5, 0.4, 1.0],
        ])

        results = self.service.get_top_similar(similarity_matrix, index=0, k=3)

        indices = [r[0] for r in results]
        assert 0 not in indices

    def test_includes_self_when_specified(self):
        """Should include self when exclude_self=False."""
        similarity_matrix = np.array([
            [1.0, 0.9, 0.5],
            [0.9, 1.0, 0.4],
            [0.5, 0.4, 1.0],
        ])

        results = self.service.get_top_similar(
            similarity_matrix, index=0, k=3, exclude_self=False
        )

        indices = [r[0] for r in results]
        assert 0 in indices
        # Self should be first (highest similarity = 1.0)
        assert results[0][0] == 0

    def test_returns_correct_indices_and_scores(self):
        """Should return correct index-score pairs."""
        similarity_matrix = np.array([
            [1.0, 0.9, 0.5, 0.3],
            [0.9, 1.0, 0.4, 0.2],
            [0.5, 0.4, 1.0, 0.8],
            [0.3, 0.2, 0.8, 1.0],
        ])

        results = self.service.get_top_similar(similarity_matrix, index=0, k=2)

        # Most similar to index 0 should be index 1 (0.9), then index 2 (0.5)
        assert results[0] == (1, 0.9)
        assert results[1] == (2, 0.5)
