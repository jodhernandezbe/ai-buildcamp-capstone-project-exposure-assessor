"""Section 2: the chemical's identity, properties with their sources, and read-across outcome."""

from __future__ import annotations

from docx.document import Document

from api.schemas.workspace import Chemical, ReadAcross, WorkspaceState
from api.services.report.document import ReportContext, paragraph, subheading, table

# Keys of ``Chemical.sources`` (the properties tool's field names) and how the report names them.
PROPERTY_LABELS = {"molecular_weight": "Molecular weight", "rfc": "RfC", "iur": "IUR"}
_KIND_LABELS = {
    "not_evaluated": "Not evaluated",
    "direct_tri_match": "Direct TRI match",
    "tri_category_member": "Member of a TRI chemical category",
    "read_across": "Read-across surrogate",
    "unresolved": "Unresolved",
}


def property_label(key: str) -> str:
    """How the report names a property source key; unknown keys are printed as given."""
    return PROPERTY_LABELS.get(key, key)


def _source(chemical: Chemical, key: str, value: float | None, ctx: ReportContext) -> str:
    if value is None:
        return ""
    return ctx.fmt.text(chemical.sources.get(key))


def _properties(chemical: Chemical, ctx: ReportContext) -> list[list[str]]:
    fmt = ctx.fmt
    quantities = (
        ("molecular_weight", chemical.molecular_weight_g_mol, "g/mol"),
        ("rfc", chemical.rfc_mg_m3, "mg/m³"),
        ("iur", chemical.iur_per_ug_m3, "(µg/m³)⁻¹"),
    )
    return [
        ["CAS number", fmt.text(chemical.cas_number), ""],
        ["Name", fmt.text(chemical.name), ""],
        *(
            [property_label(key), fmt.number(value, unit), _source(chemical, key, value, ctx)]
            for key, value, unit in quantities
        ),
    ]


def _surrogate(read_across: ReadAcross, ctx: ReportContext) -> str:
    name, cas = read_across.surrogate_name, read_across.surrogate_cas
    if name and cas:
        return f"{name} (CAS {cas})"
    return ctx.fmt.text(name or (f"CAS {cas}" if cas else None))


def _read_across(read_across: ReadAcross, ctx: ReportContext) -> list[list[str]]:
    fmt = ctx.fmt
    return [
        ["Outcome", _KIND_LABELS[read_across.kind]],
        ["Surrogate", _surrogate(read_across, ctx)],
        ["Hybrid score", fmt.number(read_across.hybrid_score)],
        ["Cosine similarity", fmt.number(read_across.cosine_similarity)],
        ["Tanimoto similarity", fmt.number(read_across.tanimoto_similarity)],
        ["Within applicability domain", fmt.flag(read_across.within_applicability_domain)],
    ]


def write_chemical(doc: Document, state: WorkspaceState, ctx: ReportContext) -> None:
    """Identity and property table, then the read-across outcome."""
    chemical = state.chemical
    table(doc, ("Property", "Value", "Source"), _properties(chemical, ctx))
    subheading(doc, "Read-across")
    if chemical.read_across.kind == "not_evaluated":
        paragraph(doc, "Read-across was not evaluated for this chemical.")
        return
    table(doc, ("Item", "Value"), _read_across(chemical.read_across, ctx))
