from dataclasses import dataclass

import numpy as np

from isw.shared.logging.logger import logger


@dataclass
class RevenueBuckets:
    """Dynamic revenue buckets computed from data."""

    boundaries: np.ndarray  # n+1 boundaries for n buckets (in original scale)
    log_boundaries: np.ndarray  # boundaries in log scale
    n_buckets: int
    min_revenue: float
    max_revenue: float

    def get_bucket_index(self, revenue: float) -> int:
        """Get bucket index for a revenue value (0-indexed)."""
        if revenue < 0 or np.isnan(revenue):
            return -1  # Invalid
        log_rev = np.log1p(revenue)
        idx = int(np.searchsorted(self.log_boundaries[1:], log_rev, side="right"))
        return min(idx, self.n_buckets - 1)

    def get_bucket_indices(self, revenues: np.ndarray) -> np.ndarray:
        """Vectorized bucket assignment for multiple revenues."""
        revenues = np.asarray(revenues, dtype=np.float64)
        log_revs = np.log1p(np.maximum(revenues, 0))  # Clamp negatives to 0 for log
        indices = np.searchsorted(self.log_boundaries[1:], log_revs, side="right")
        indices = np.clip(indices, 0, self.n_buckets - 1)

        # Mark invalid entries
        invalid_mask = (revenues < 0) | np.isnan(revenues)
        indices = indices.astype(np.int64)
        indices[invalid_mask] = -1
        return indices


@dataclass
class RevenueSimilarityResult:
    """Result of revenue similarity computation."""

    similarity_matrix: np.ndarray
    log_revenues: np.ndarray
    valid_mask: np.ndarray  # True for entries with valid (non-missing) revenue
    scale: float  # Scale parameter used for exponential decay
    buckets: RevenueBuckets
    bucket_assignments: np.ndarray  # Bucket index for each company


class RevenueSimilarityService:
    """Service for computing revenue-based similarity using log-scale proximity."""

    def __init__(
        self,
        n_buckets: int = 20,
        scale: float | None = None,
        missing_value_strategy: str = "median",
    ):
        """
        Initialize revenue similarity service.

        Args:
            n_buckets: Number of revenue buckets to create from data range.
            scale: Scale parameter for exponential decay. If None, uses std of log revenues.
            missing_value_strategy: How to handle missing revenue values.
                - "median": Replace with median of valid revenues
                - "exclude": Mark as invalid (similarity will be 0)
        """
        if missing_value_strategy not in ("median", "exclude"):
            raise ValueError("missing_value_strategy must be 'median' or 'exclude'")
        if n_buckets < 1:
            raise ValueError("n_buckets must be at least 1")

        self.n_buckets = n_buckets
        self.scale = scale
        self.missing_value_strategy = missing_value_strategy

    def compute_similarity(
        self,
        revenues: np.ndarray,
    ) -> RevenueSimilarityResult:
        """
        Compute revenue similarity matrix using log-scale proximity.

        Args:
            revenues: Array of revenue values. Use np.nan or negative values for missing.

        Returns:
            RevenueSimilarityResult containing similarity matrix and metadata
        """
        revenues = np.asarray(revenues, dtype=np.float64)

        if revenues.shape[0] < 2:
            raise ValueError("Need at least 2 revenue values to compute similarity")

        logger.info("Computing revenue similarity for %d companies", revenues.shape[0])

        # Identify valid (non-missing) revenues
        valid_mask = ~np.isnan(revenues) & (revenues >= 0)
        n_valid = np.sum(valid_mask)
        n_missing = len(revenues) - n_valid

        if n_valid == 0:
            raise ValueError("All revenue values are missing or invalid")

        logger.debug("Valid revenues: %d, Missing: %d", n_valid, n_missing)

        # Compute dynamic buckets from valid data
        valid_revenues = revenues[valid_mask]
        buckets = self._compute_buckets(valid_revenues)

        # Handle missing values
        processed_revenues = revenues.copy()
        if n_missing > 0:
            if self.missing_value_strategy == "median":
                median_revenue = np.median(valid_revenues)
                processed_revenues[~valid_mask] = median_revenue
                logger.debug("Replaced %d missing values with median: %.2f", n_missing, median_revenue)

        # Log transform (log1p handles zero revenue)
        log_revenues = np.log1p(processed_revenues)

        # Assign bucket indices (vectorized)
        bucket_assignments = buckets.get_bucket_indices(processed_revenues)

        # Compute pairwise absolute differences in log space
        log_rev_i = log_revenues.reshape(-1, 1)
        log_rev_j = log_revenues.reshape(1, -1)
        log_diff = np.abs(log_rev_i - log_rev_j)

        # Determine scale parameter
        if self.scale is not None:
            effective_scale = self.scale
        else:
            valid_log_revenues = log_revenues[valid_mask]
            std = np.std(valid_log_revenues)
            effective_scale = std if std > 0 else 1.0

        logger.debug("Using scale parameter: %.4f", effective_scale)

        # Convert to similarity using exponential decay
        similarity_matrix = np.exp(-log_diff / effective_scale)

        # For "exclude" strategy, set similarity to 0 for missing values
        if self.missing_value_strategy == "exclude" and n_missing > 0:
            invalid_indices = np.where(~valid_mask)[0]
            similarity_matrix[invalid_indices, :] = 0
            similarity_matrix[:, invalid_indices] = 0
            np.fill_diagonal(similarity_matrix, np.where(valid_mask, 1.0, 0.0))

        return RevenueSimilarityResult(
            similarity_matrix=similarity_matrix,
            log_revenues=log_revenues,
            valid_mask=valid_mask,
            scale=effective_scale,
            buckets=buckets,
            bucket_assignments=bucket_assignments,
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

    def _compute_buckets(self, revenues: np.ndarray) -> RevenueBuckets:
        """Compute dynamic buckets from revenue data using log scale."""
        min_rev = float(np.min(revenues))
        max_rev = float(np.max(revenues))

        # Use log scale for even distribution across orders of magnitude
        log_min = np.log1p(min_rev)
        log_max = np.log1p(max_rev)

        # Create n+1 boundaries for n buckets (evenly spaced in log scale)
        log_boundaries = np.linspace(log_min, log_max, self.n_buckets + 1)
        boundaries = np.expm1(log_boundaries)

        return RevenueBuckets(
            boundaries=boundaries,
            log_boundaries=log_boundaries,
            n_buckets=self.n_buckets,
            min_revenue=min_rev,
            max_revenue=max_rev,
        )
