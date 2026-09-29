import re
from typing import Dict, Any, List, Optional, Callable, Tuple
from app.utils.logger import logger


class NarrativeEngine:
    """
    Generates plain-language district planning briefs.

    TEMPLATE FIRST: the brief is always built from a fixed template containing
    placeholders such as {demand_count}. An LLM (provider behind
    settings.AI_PROVIDER, default 'mock') may only REWRITE the template's
    sentences - it never sees or produces numbers. All placeholders are
    substituted with query-derived values by code AFTER generation.

    Safety: the validator rejects any LLM output that (a) drops or mangles a
    placeholder, or (b) contains a digit sequence that is not present in the
    query result. Rejected output falls back to the raw template, so every
    published figure traces back to the aggregation query.
    """

    TEMPLATE = """DISTRICT PLANNING BRIEF - {district} - {period}
Generated {generated_at} | Source query: {query_id}

1. DEMAND OVERVIEW
During {period}, {demand_count} anonymised demand records were collected across {block_count} blocks in {district}. Of these, {verified_match_count} records ({verified_match_share}) had a Verified Match to a worker-verified local training batch.

2. PRIORITY GAPS (ranked by severity = demand_count x (1 - coverage) x distance penalty)
{gap_lines}

3. ACCESS RISK
{access_line}

4. DATA QUALITY AND PRIVACY
{suppressed_count} block-trade cells were suppressed under k-anonymity (cells with fewer than {k_threshold} demand records are not reported). Supply figures count only worker-verified, non-stale, non-archived batches. Every figure in this brief derives solely from database query {query_id}; row-level source references are stored in the aggregation snapshot attached to this brief.

5. RECOMMENDED ACTIONS
{action_lines}
"""

    GAP_LINE = "- {block}, {qualification_title}: {demand_count} expressed interest vs {verified_seats} verified seats (gap {gap}); nearest verified centre {nearest_km} km away; severity {severity}."
    GAP_LINE_NO_CENTRE = "- {block}, {qualification_title}: {demand_count} expressed interest vs {verified_seats} verified seats (gap {gap}); no worker-verified centre exists anywhere in {district}; severity {severity}."
    ACTION_SANCTION = "- Sanction additional worker-verified {qualification_title} batches in {block}; unmet demand is {gap} seats against {demand_count} expressions of interest."
    ACTION_MOBILE = "- Deploy a mobile skilling unit for {qualification_title} in {block}: the nearest verified centre is {nearest_km} km away, beyond the {distance_cap_km} km planning threshold."

    # ------------------------------------------------------------------
    # Template construction (all values come from the query result)
    # ------------------------------------------------------------------
    @staticmethod
    def build_brief_data(matrix: Dict[str, Any]) -> Dict[str, Any]:
        """Flattens the aggregation result into placeholder -> value pairs."""
        metrics = matrix.get("metrics", {})
        cells = [c for c in matrix.get("matrix", []) if not c.get("suppressed")]
        top = cells[0] if cells else {}
        second = cells[1] if len(cells) > 1 else {}
        third = cells[2] if len(cells) > 2 else {}

        data: Dict[str, Any] = {
            "district": matrix.get("district", ""),
            "period": matrix.get("period") or "all periods",
            "generated_at": matrix.get("generated_at", ""),
            "query_id": matrix.get("query_id", ""),
            "demand_count": metrics.get("total_demand_records", 0),
            "block_count": metrics.get("blocks_with_demand", 0),
            "verified_match_count": metrics.get("demand_with_verified_match_count", 0),
            "verified_match_share": _fmt_share(metrics.get("demand_with_verified_match_share", 0.0)),
            "suppressed_count": metrics.get("suppressed_cell_count", 0),
            "k_threshold": matrix.get("data_basis", {}).get("k_anonymity_threshold", 5),
            "distance_cap_km": matrix.get("data_basis", {}).get("distance_cap_km", 50),
            "supply_batches": metrics.get("supply_batches_considered", 0),
            "total_unmet_demand": metrics.get("total_unmet_demand", 0),
            "gap_lines": _gap_lines(matrix.get("district", ""), cells),
            "access_line": _access_line(matrix.get("district", ""), cells),
            "action_lines": _action_lines(cells),
        }
        for label, cell in (("top", top), ("second", second), ("third", third)):
            if cell:
                data[f"{label}_block"] = cell["block"]
                data[f"{label}_qualification_title"] = cell["qualification_title"]
                data[f"{label}_demand_count"] = cell["demand_count"]
                data[f"{label}_verified_seats"] = cell["verified_seats"]
                data[f"{label}_gap"] = cell["gap"]
                data[f"{label}_nearest_km"] = cell["nearest_verified_centre_km"]
                data[f"{label}_severity"] = cell["severity_score"]
                data[f"{label}_share_no_batch"] = cell["share_of_demand_with_no_verified_batch"]
        return data

    # ------------------------------------------------------------------
    # LLM rewrite + validation
    # ------------------------------------------------------------------
    @staticmethod
    def _allowed_digits(brief_data: Dict[str, Any]) -> set:
        """
        Every digit sequence that may legally appear in LLM output: the
        string form of every numeric value in the query result, plus digit
        sequences inside string values (period, district, timestamps).
        """
        allowed = set()

        # Digits in the template's own static text (section numbers etc.)
        # are code, not LLM output, so they are always legal.
        for seq in re.findall(r"\d+", NarrativeEngine.TEMPLATE):
            allowed.add(seq)

        def add_value(v: Any) -> None:
            if isinstance(v, bool):
                return
            if isinstance(v, (int, float)):
                allowed.add(str(v))
                if isinstance(v, float):
                    allowed.add(str(int(v)))
                    allowed.add(f"{v:.1f}")
            elif isinstance(v, str):
                for seq in re.findall(r"\d+", v):
                    allowed.add(seq)

        for value in brief_data.values():
            if isinstance(value, list):
                for item in value:
                    add_value(item)
            else:
                add_value(value)
        return allowed

    @staticmethod
    def validate_llm_output(text: str, brief_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Returns (ok, reason). Rejects output that invents numbers or drops
        placeholders - the LLM may only rephrase, never add figures.
        """
        template_placeholders = set(re.findall(r"\{([a-z_]+)\}", NarrativeEngine.TEMPLATE))
        for name in template_placeholders:
            if f"{{{name}}}" not in text:
                return False, f"missing_placeholder:{name}"
        allowed = NarrativeEngine._allowed_digits(brief_data)
        for seq in re.findall(r"\d+", text):
            if seq not in allowed:
                return False, f"invented_number:{seq}"
        return True, "passed"

    @staticmethod
    def _default_llm_rewrite(template: str) -> str:
        """
        Provider behind settings.AI_PROVIDER (default 'mock'). 'mock' returns
        the template unchanged. Any other provider requires AI_API_KEY; on
        any failure the caller falls back to the template.
        """
        from app.core.settings import settings

        if settings.AI_PROVIDER == "mock" or not settings.AI_API_KEY:
            return template
        raise RuntimeError(
            f"LLM rewrite not available for provider '{settings.AI_PROVIDER}' "
            "without a configured client; using template."
        )

    @staticmethod
    def _substitute(text: str, brief_data: Dict[str, Any]) -> Tuple[str, bool]:
        """Replaces {placeholder} tokens. Returns (text, all_resolved)."""
        result = text
        unresolved = False
        for name, value in brief_data.items():
            token = f"{{{name}}}"
            if token in result:
                if isinstance(value, list):
                    value = "\n".join(str(v) for v in value)
                result = result.replace(token, str(value))
            if token in result:
                unresolved = True
        leftovers = re.findall(r"\{[a-z_]+\}", result)
        if leftovers:
            unresolved = True
        return result, not unresolved

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @staticmethod
    def generate_brief(
        matrix: Dict[str, Any],
        llm_rewrite: Optional[Callable[[str], str]] = None,
    ) -> Dict[str, Any]:
        """
        Builds the brief: template -> optional LLM rewrite -> validation ->
        placeholder substitution. Falls back to the template on any
        validation failure. Returns the text plus provenance metadata and
        per-figure source references.
        """
        brief_data = NarrativeEngine.build_brief_data(matrix)
        raw_template = NarrativeEngine.TEMPLATE  # placeholders intact for the LLM

        provider = "mock"
        rewritten = False
        validation = "not_requested"
        final_text = raw_template

        from app.core.settings import settings

        rewrite_fn = llm_rewrite or NarrativeEngine._default_llm_rewrite
        using_mock_default = llm_rewrite is None and (
            settings.AI_PROVIDER == "mock" or not settings.AI_API_KEY
        )
        try:
            candidate = rewrite_fn(raw_template)
            ok, reason = NarrativeEngine.validate_llm_output(candidate, brief_data)
            if ok:
                final_text = candidate
                rewritten = candidate != raw_template
                validation = "passed"
                provider = "mock" if using_mock_default else "llm"
            else:
                validation = f"fallback:{reason}"
                logger.warning(f"LLM brief rejected ({reason}); using template.")
        except Exception as e:
            validation = f"fallback:llm_error:{e}"
            logger.warning(f"LLM brief unavailable ({e}); using template.")

        # Numbers are inserted by code AFTER generation - never by the LLM.
        final_text, resolved = NarrativeEngine._substitute(final_text, brief_data)
        if not resolved:
            # LLM mangled a placeholder beyond validation - regenerate safely.
            final_text, resolved = NarrativeEngine._substitute(raw_template, brief_data)
            validation = f"{validation}:re_substituted_from_template"
            rewritten = False

        return {
            "narrative": final_text,
            "narrative_meta": {
                "provider": provider,
                "rewritten_by_llm": rewritten,
                "validation": validation,
                "template_first": True,
            },
            "figures": NarrativeEngine._figure_sources(matrix, brief_data),
        }

    @staticmethod
    def _figure_sources(matrix: Dict[str, Any], brief_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Attaches a source reference (query id + row ids) to every figure."""
        figures: List[Dict[str, Any]] = []
        query_id = matrix.get("query_id", "")
        cells = matrix.get("matrix", [])

        def cell_for(block: str, title: str) -> Optional[Dict[str, Any]]:
            for c in cells:
                if c["block"] == block and c["qualification_title"] == title:
                    return c
            return None

        metrics = matrix.get("metrics", {})
        figures.append({
            "figure": "total_demand_records",
            "value": metrics.get("total_demand_records"),
            "source_query_id": query_id,
            "source_table": "demand_records",
            "source_row_ids": [],
            "note": "Count of anonymised demand records for the district/period; row ids stored in the aggregation snapshot cells.",
        })
        for label in ("top", "second", "third"):
            block = brief_data.get(f"{label}_block")
            title = brief_data.get(f"{label}_qualification_title")
            if not block:
                continue
            cell = cell_for(block, title)
            if not cell:
                continue
            src = cell.get("source", {})
            figures.append({
                "figure": f"{label}_gap",
                "value": {
                    "block": block,
                    "qualification_title": title,
                    "demand_count": cell.get("demand_count"),
                    "verified_seats": cell.get("verified_seats"),
                    "gap": cell.get("gap"),
                    "nearest_verified_centre_km": cell.get("nearest_verified_centre_km"),
                    "severity_score": cell.get("severity_score"),
                },
                "source_query_id": src.get("query_id", query_id),
                "source_table": "demand_records + local_opportunities",
                "source_row_ids": (src.get("demand_row_ids") or []) + (src.get("supply_batch_ids") or []),
            })
        return figures


def _fmt_share(share: float) -> str:
    return f"{share * 100:.1f}%"


def _gap_lines(district: str, cells: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for c in cells[:3]:
        if c.get("nearest_verified_centre_km") is None:
            lines.append(NarrativeEngine.GAP_LINE_NO_CENTRE.format(
                block=c["block"],
                qualification_title=c["qualification_title"],
                demand_count=c["demand_count"],
                verified_seats=c["verified_seats"],
                gap=c["gap"],
                district=district,
                severity=c["severity_score"],
            ))
        else:
            lines.append(NarrativeEngine.GAP_LINE.format(
                block=c["block"],
                qualification_title=c["qualification_title"],
                demand_count=c["demand_count"],
                verified_seats=c["verified_seats"],
                gap=c["gap"],
                nearest_km=c["nearest_verified_centre_km"],
                severity=c["severity_score"],
            ))
    if not lines:
        lines.append("- No block-trade cells met the k-anonymity threshold (5 demand records); no gaps can be reported without risking re-identification.")
    return lines


def _access_line(district: str, cells: List[Dict[str, Any]]) -> str:
    no_centre = [c for c in cells if c.get("nearest_verified_centre_km") is None]
    far = [c for c in cells if c.get("nearest_verified_centre_km") is not None
           and c["nearest_verified_centre_km"] > 50]
    if no_centre:
        blocks = ", ".join(sorted({c["block"] for c in no_centre}))
        return (
            f"In {blocks}, no worker-verified training centre exists anywhere in {district} "
            f"for the demanded trades, so demand there can only be met by mobile units or new batches."
        )
    if far:
        c = far[0]
        return (
            f"{c['block']} has demand for {c['qualification_title']} but the nearest verified "
            f"centre is {c['nearest_verified_centre_km']} km away, beyond the 50 km planning threshold."
        )
    return "Every demanded trade has a worker-verified centre within 50 km of the demanding blocks."


def _action_lines(cells: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for c in cells[:2]:
        if c.get("gap") is not None and c["gap"] > 0:
            lines.append(NarrativeEngine.ACTION_SANCTION.format(
                qualification_title=c["qualification_title"],
                block=c["block"],
                gap=c["gap"],
                demand_count=c["demand_count"],
            ))
        if c.get("nearest_verified_centre_km") is not None and c["nearest_verified_centre_km"] > 50:
            lines.append(NarrativeEngine.ACTION_MOBILE.format(
                qualification_title=c["qualification_title"],
                block=c["block"],
                nearest_km=c["nearest_verified_centre_km"],
                distance_cap_km=50,
            ))
    if not lines:
        lines.append("- No sanctionable gaps met the reporting threshold; maintain existing verified capacity.")
    return lines
