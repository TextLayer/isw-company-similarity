from dataclasses import dataclass

import hdbscan
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from umap import UMAP

from isw.shared.logging.logger import logger


@dataclass
class EmbeddingSimilarityResult:
    """Result of embedding similarity computation."""

    similarity_matrix: np.ndarray
    cluster_labels: np.ndarray
    reduced_embeddings: np.ndarray
    noise_mask: np.ndarray  # True for noise points (label == -1)


class EmbeddingSimilarityService:
    """Service for computing embedding-based similarity using UMAP and HDBSCAN."""

    def __init__(
        self,
        # UMAP parameters
        n_components: int = 50,
        n_neighbors: int = 30,
        min_dist: float = 0.0,
        umap_metric: str = "cosine",
        # HDBSCAN parameters
        min_cluster_size: int = 10,
        min_samples: int = 5,
        hdbscan_metric: str = "euclidean",
    ):
        self.n_components = n_components
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.umap_metric = umap_metric
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.hdbscan_metric = hdbscan_metric

    def compute_similarity(
        self,
        embeddings: np.ndarray,
        random_state: int | None = 42,
    ) -> EmbeddingSimilarityResult:
        """
        Compute embedding similarity using UMAP reduction and HDBSCAN clustering.

        The similarity matrix is computed using cosine similarity in the UMAP-reduced
        embedding space. HDBSCAN cluster labels and noise mask are provided as metadata
        for callers to use as needed (e.g., filtering out noise points or analyzing
        cluster structure), but do not directly influence the similarity scores.

        Args:
            embeddings: Matrix of shape (n_samples, n_features) containing embeddings
            random_state: Random seed for reproducibility (None for non-deterministic)

        Returns:
            EmbeddingSimilarityResult containing similarity matrix, cluster labels,
            reduced embeddings, and noise mask
        """
        if embeddings.ndim != 2:
            raise ValueError(f"embeddings must be 2D array, got {embeddings.ndim}D")
        if embeddings.shape[0] < 2:
            raise ValueError("Need at least 2 embeddings to compute similarity")

        n_samples = embeddings.shape[0]
        logger.info(
            "Computing embedding similarity for %d samples with %d dimensions",
            n_samples,
            embeddings.shape[1],
        )

        # Adjust parameters for small datasets
        # UMAP requires n_components < n_samples for spectral embedding
        effective_n_neighbors = min(self.n_neighbors, n_samples - 1)
        effective_n_components = min(self.n_components, embeddings.shape[1], n_samples - 2)
        effective_n_components = max(2, effective_n_components)  # At least 2 components
        effective_min_cluster_size = min(self.min_cluster_size, max(2, n_samples // 5))
        effective_min_samples = min(self.min_samples, effective_min_cluster_size)

        # 1. UMAP dimensionality reduction
        logger.debug(
            "Running UMAP: n_components=%d, n_neighbors=%d",
            effective_n_components,
            effective_n_neighbors,
        )
        reducer = UMAP(
            n_components=effective_n_components,
            n_neighbors=effective_n_neighbors,
            min_dist=self.min_dist,
            metric=self.umap_metric,
            random_state=random_state,
        )
        reduced = reducer.fit_transform(embeddings)
        logger.debug("UMAP reduction complete: %s -> %s", embeddings.shape, reduced.shape)

        # 2. HDBSCAN clustering
        logger.debug(
            "Running HDBSCAN: min_cluster_size=%d, min_samples=%d",
            effective_min_cluster_size,
            effective_min_samples,
        )
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=effective_min_cluster_size,
            min_samples=effective_min_samples,
            metric=self.hdbscan_metric,
        )
        cluster_labels = clusterer.fit_predict(reduced)

        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = np.sum(cluster_labels == -1)
        logger.info("HDBSCAN found %d clusters, %d noise points", n_clusters, n_noise)

        # 3. Compute cosine similarity in reduced space
        similarity_matrix = cosine_similarity(reduced)

        # 4. Create noise mask
        noise_mask = cluster_labels == -1

        return EmbeddingSimilarityResult(
            similarity_matrix=similarity_matrix,
            cluster_labels=cluster_labels,
            reduced_embeddings=reduced,
            noise_mask=noise_mask,
        )

    def get_top_similar(
        self,
        similarity_matrix: np.ndarray,
        index: int,
        k: int = 10,
        exclude_self: bool = True,
    ) -> list[tuple[int, float]]:
        """
        Get top-k most similar items for a given index.

        Args:
            similarity_matrix: Precomputed similarity matrix
            index: Index of the item to find similar items for
            k: Number of similar items to return
            exclude_self: Whether to exclude the item itself from results

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity descending
        """
        if index < 0 or index >= similarity_matrix.shape[0]:
            raise ValueError(f"index {index} out of bounds for matrix with {similarity_matrix.shape[0]} rows")

        similarities = similarity_matrix[index]

        # Get indices sorted by similarity (descending)
        sorted_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in sorted_indices:
            if exclude_self and idx == index:
                continue
            results.append((int(idx), float(similarities[idx])))
            if len(results) >= k:
                break

        return results
