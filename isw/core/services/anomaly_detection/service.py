from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from sqlalchemy.orm import Session

from ...models.company_models import CompanyFacts


@dataclass
class AnomalyDetectionConfig:
    """Configuration for anomaly detection thresholds. Single source of truth for all defaults."""
    common_threshold: float = 0.70      # Tag is "expected" if >= 70% of peers have it
    rare_threshold: float = 0.3        # Tag is "unexpected" if <= 25% of peers have it
    conf_level: float = 0.85            # 85% confidence interval
    use_confidence_intervals: bool = True  # Use CI lower/upper bounds vs point estimates
    min_peers: int = 5                  # Minimum peers required
    n_peers: int = 10                   # Default number of peers to compare
    similarity_threshold: float = 0.5   # Minimum similarity for peer selection
    filter_community: bool = True       # Filter peers by Leiden community


class XBRLAnomalyService:
    """Service for detecting XBRL tag anomalies in company filings."""
    
    @staticmethod
    def _get_z_score(conf_level: float) -> float:
        """Get z-score for confidence level."""
        z_scores = {
            0.90: 1.645,
            0.95: 1.960,
            0.99: 2.576,
        }
        return z_scores.get(conf_level, 1.960)
    
    @staticmethod
    def _wilson_interval(count: int, total: int, conf_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate Wilson score confidence interval for a proportion.
        
        Args:
            count: Number of successes
            total: Total number of trials
            conf_level: Confidence level
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if total == 0:
            return 0.0, 1.0
        
        z = XBRLAnomalyService._get_z_score(conf_level)
        p = count / total
        
        denominator = 1 + z**2 / total
        center = (p + z**2 / (2 * total)) / denominator
        margin = (z / denominator) * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2))
        
        lower = max(0.0, center - margin)
        upper = min(1.0, center + margin)
        
        return lower, upper
    
    @staticmethod
    def get_company_tags(
        session: Session,
        cik: int,
        form_type: str,
        fiscal_year: Optional[str] = None,
        filing_period: Optional[str] = None
    ) -> set:
        """Get unique XBRL tags for a company's filings."""
        query = session.query(CompanyFacts.fact).filter(
            CompanyFacts.cik == cik,
            CompanyFacts.form_type == form_type
        )
        
        if fiscal_year:
            query = query.filter(CompanyFacts.fiscal_year == fiscal_year)
        if filing_period:
            query = query.filter(CompanyFacts.filing_period == filing_period)
        
        return {row[0] for row in query.distinct().all()}
    
    @staticmethod
    def detect_anomalies(
        session: Session,
        target_cik: int,
        peer_ciks: List[int],
        form_type: str,
        fiscal_year: Optional[str] = None,
        filing_period: Optional[str] = None,
        common_threshold: float = 0.80,
        rare_threshold: float = 0.10,
        min_peers: int = 5
    ) -> Dict[str, Any]:
        """
        Detect XBRL tag anomalies by comparing target against peers.
        
        Missing tags: Common in peers (≥80%) but absent in target
        Extra tags: Rare in peers (≤10%) but present in target
        
        Args:
            session: Database session
            target_cik: Target company CIK
            peer_ciks: List of peer CIKs
            form_type: Report form (10-K or 10-Q)
            fiscal_year: Optional fiscal year filter
            filing_period: Optional filing period filter
            common_threshold: Threshold for "expected" tags (default 0.80)
            rare_threshold: Threshold for "unexpected" tags (default 0.10)
            min_peers: Minimum peers required (default 5)
            
        Returns:
            Dictionary with missing_tags, extra_tags, and summary
        """
        # Validate peers
        if len(peer_ciks) < min_peers:
            return {
                'missing_tags': [],
                'extra_tags': [],
                'summary': {
                    'error': f'Insufficient peers: {len(peer_ciks)} (minimum required: {min_peers})',
                    'target_cik': target_cik,
                    'form_type': form_type
                }
            }
        
        # Get target's tags
        target_tags = XBRLAnomalyService.get_company_tags(
            session, target_cik, form_type, fiscal_year, filing_period
        )
        
        if not target_tags:
            return {
                'missing_tags': [],
                'extra_tags': [],
                'summary': {
                    'error': 'No filings found for target company',
                    'target_cik': target_cik,
                    'form_type': form_type
                }
            }
        
        # Count tag occurrences across peers
        peer_tag_counts = {}
        for peer_cik in peer_ciks:
            peer_tags = XBRLAnomalyService.get_company_tags(session, peer_cik, form_type)
            for tag in peer_tags:
                peer_tag_counts[tag] = peer_tag_counts.get(tag, 0) + 1
        
        n_peers = len(peer_ciks)
        
        # Detect missing tags (common in peers but absent in target)
        missing_tags = []
        all_peer_tags = set(peer_tag_counts.keys())
        
        for tag in all_peer_tags:
            if tag in target_tags:
                continue
            
            peer_count = peer_tag_counts[tag]
            peer_freq = peer_count / n_peers
            
            # Use Wilson confidence interval lower bound for conservative estimate
            ci_lower, _ = XBRLAnomalyService._wilson_interval(peer_count, n_peers, 0.95)
            
            # Missing if lower bound of CI exceeds threshold (conservative)
            if ci_lower >= common_threshold:
                missing_tags.append({
                    'tag': tag,
                    'peer_frequency': round(peer_freq, 3),
                    'peer_count': peer_count,
                    'confidence_lower': round(ci_lower, 3),
                    'severity': round(ci_lower - common_threshold, 3)
                })
        
        # Detect extra tags (rare in peers but present in target)
        extra_tags = []
        
        for tag in target_tags:
            peer_count = peer_tag_counts.get(tag, 0)
            peer_freq = peer_count / n_peers if n_peers > 0 else 0
            
            # Use Wilson confidence interval upper bound for conservative estimate
            _, ci_upper = XBRLAnomalyService._wilson_interval(peer_count, n_peers, 0.95)
            
            # Extra if upper bound of CI is below threshold (conservative)
            if ci_upper <= rare_threshold:
                extra_tags.append({
                    'tag': tag,
                    'peer_frequency': round(peer_freq, 3),
                    'peer_count': peer_count,
                    'confidence_upper': round(ci_upper, 3),
                    'severity': round(rare_threshold - ci_upper, 3)
                })
        
        # Sort by severity (most severe first)
        missing_tags.sort(key=lambda x: x['severity'], reverse=True)
        extra_tags.sort(key=lambda x: x['severity'], reverse=True)
        
        # Limit to top anomalies
        missing_tags = missing_tags[:50]
        extra_tags = extra_tags[:50]
        
        summary = {
            'target_cik': target_cik,
            'form_type': form_type,
            'fiscal_year': fiscal_year,
            'filing_period': filing_period,
            'n_peers': n_peers,
            'n_missing_tags': len(missing_tags),
            'n_extra_tags': len(extra_tags),
            'total_target_tags': len(target_tags),
            'thresholds': {
                'common_threshold': common_threshold,
                'rare_threshold': rare_threshold
            }
        }
        
        return {
            'missing_tags': missing_tags,
            'extra_tags': extra_tags,
            'summary': summary
        }

