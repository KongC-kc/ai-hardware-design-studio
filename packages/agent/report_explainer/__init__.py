"""Rule-based report explanation helpers."""

from packages.agent.report_explainer.erc_explainer import ErcExplanationResult, explain_erc_report
from packages.agent.report_explainer.erc_fix_suggester import ErcSuggestedFixesResult, suggest_erc_fixes

__all__ = ["ErcExplanationResult", "ErcSuggestedFixesResult", "explain_erc_report", "suggest_erc_fixes"]
