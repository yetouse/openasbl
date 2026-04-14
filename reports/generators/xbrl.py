"""
XBRL generator for Belgian BNB filing — micro model (m08).

Generates an XBRL instance document following the NBB CBSO taxonomy 26.0
for micro associations (ASBL). This covers the simplified annual accounts
that small Belgian non-profits must file with the Banque Nationale de Belgique.

Mapping from OpenASBL to BNB rubrics:
- AssetSnapshot.cash + bank → bas:m23 (Valeurs disponibles)
- AssetSnapshot.receivables → bas:m15 (Créances à un an au plus)
- AssetSnapshot.debts → bas:m50 (Dettes)
- Total income → bas:m133 (Cotisations, dons, legs, subsides)
- Total expenses → bas:m136 (Charges)
- Result → bas:m59 (Résultat de l'exercice)
"""

from datetime import date
from decimal import Decimal
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, tostring

from accounting.models import AssetSnapshot, CategoryType, Entry

# Namespaces
NS = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrldi": "http://xbrl.org/2006/xbrldi",
    "iso4217": "http://www.xbrl.org/2003/iso4217",
    "met": "http://www.nbb.be/be/fr/cbso/dict/met",
    "dim": "http://www.nbb.be/be/fr/cbso/dict/dim",
    "bas": "http://www.nbb.be/be/fr/cbso/dict/dom/bas",
    "part": "http://www.nbb.be/be/fr/cbso/dict/dom/part",
    "prd": "http://www.nbb.be/be/fr/cbso/dict/dom/prd",
}

SCHEMA_REF = "http://www.nbb.be/be/fr/cbso/fws/26.0/mod/m08/m08-f.xsd"
ENTITY_SCHEME = "http://www.fgov.be"


def _clean_enterprise_number(raw: str) -> str:
    """Extract digits-only enterprise number (e.g., '0413.726.972' → '0413726972')."""
    return "".join(c for c in raw if c.isdigit())


def _fmt_amount(amount: Decimal) -> str:
    """Format decimal to string with 2 decimal places for XBRL."""
    return str(amount.quantize(Decimal("0.01")))


def _add_context(root, ctx_id, entity_id, instant_date, dimensions):
    """Add an XBRL context element with dimensional scenario."""
    X = NS["xbrli"]
    ctx = SubElement(root, f"{{{X}}}context", id=ctx_id)
    entity = SubElement(ctx, f"{{{X}}}entity")
    identifier = SubElement(entity, f"{{{X}}}identifier", scheme=ENTITY_SCHEME)
    identifier.text = entity_id

    period = SubElement(ctx, f"{{{X}}}period")
    instant = SubElement(period, f"{{{X}}}instant")
    instant.text = instant_date.isoformat()

    if dimensions:
        scenario = SubElement(ctx, f"{{{X}}}scenario")
        for dim_name, member in dimensions:
            em = SubElement(
                scenario,
                "{http://xbrl.org/2006/xbrldi}explicitMember",
                dimension=dim_name,
            )
            em.text = member

    return ctx


def _add_fact(root, metric, ctx_id, value, unit_ref="EUR", decimals="INF"):
    """Add an XBRL fact element."""
    ns_uri = NS["met"]
    fact = SubElement(root, f"{{{ns_uri}}}{metric}", contextRef=ctx_id, unitRef=unit_ref, decimals=decimals)
    fact.text = value
    return fact


def generate_xbrl(fiscal_year):
    """
    Generate an XBRL instance document for the given fiscal year.

    Returns XML bytes (UTF-8 encoded).
    """
    org = fiscal_year.organization
    entity_id = _clean_enterprise_number(org.enterprise_number or "0000000000")
    end_date = fiscal_year.end_date

    # Aggregate financial data
    entries = Entry.objects.filter(fiscal_year=fiscal_year).select_related("category")
    total_income = Decimal("0")
    total_expense = Decimal("0")
    for entry in entries:
        if entry.entry_type == CategoryType.INCOME:
            total_income += entry.amount
        else:
            total_expense += entry.amount
    result = total_income - total_expense

    # Get closing asset snapshot (latest for this fiscal year)
    closing_snapshot = (
        AssetSnapshot.objects.filter(fiscal_year=fiscal_year).order_by("-date").first()
    )

    # Balance sheet values
    if closing_snapshot:
        cash_bank = closing_snapshot.cash + closing_snapshot.bank
        receivables = closing_snapshot.receivables
        debts = closing_snapshot.debts
        total_assets = cash_bank + receivables
        equity = closing_snapshot.net_worth
    else:
        cash_bank = Decimal("0")
        receivables = Decimal("0")
        debts = Decimal("0")
        total_assets = Decimal("0")
        equity = Decimal("0")

    # Build XML tree
    # Register namespaces for clean output
    for prefix, uri in NS.items():
        if prefix == "xbrli":
            continue
        ET.register_namespace(prefix, uri)

    root = Element(
        "{http://www.xbrl.org/2003/instance}xbrl",
    )

    # Schema reference
    schema_ref = SubElement(
        root,
        "{http://www.xbrl.org/2003/linkbase}schemaRef",
    )
    schema_ref.set("{http://www.w3.org/1999/xlink}type", "simple")
    schema_ref.set("{http://www.w3.org/1999/xlink}href", SCHEMA_REF)

    # Unit EUR
    X = NS["xbrli"]
    unit_eur = SubElement(root, f"{{{X}}}unit", id="EUR")
    measure = SubElement(unit_eur, f"{{{X}}}measure")
    measure.text = "iso4217:EUR"

    # Define contexts
    ctx_counter = [0]

    def make_ctx(dimensions):
        ctx_counter[0] += 1
        ctx_id = f"c{ctx_counter[0]}"
        _add_context(root, ctx_id, entity_id, end_date, dimensions)
        return ctx_id

    # ─── BALANCE SHEET: ACTIF (part:m1) ───

    # Valeurs disponibles (cash + bank) — bas:m23, part:m1, prd:m1
    ctx_cash = make_ctx([("dim:bas", "bas:m23"), ("dim:part", "part:m1"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_cash, _fmt_amount(cash_bank))

    # Créances à un an au plus — bas:m15, part:m1, prd:m1
    ctx_recv = make_ctx([("dim:bas", "bas:m15"), ("dim:part", "part:m1"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_recv, _fmt_amount(receivables))

    # Actifs circulants (total) — bas:m12, part:m1, prd:m1
    ctx_current = make_ctx([("dim:bas", "bas:m12"), ("dim:part", "part:m1"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_current, _fmt_amount(total_assets))

    # Total actif — bas:m25, part:m1, prd:m1
    ctx_total_a = make_ctx([("dim:bas", "bas:m25"), ("dim:part", "part:m1"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_total_a, _fmt_amount(total_assets))

    # ─── BALANCE SHEET: PASSIF (part:m3) ───

    # Fonds de l'association — bas:m135, part:m3, prd:m1
    ctx_equity = make_ctx([("dim:bas", "bas:m135"), ("dim:part", "part:m3"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_equity, _fmt_amount(equity))

    # Résultat reporté — bas:m44, part:m3, prd:m1
    ctx_result_bs = make_ctx([("dim:bas", "bas:m44"), ("dim:part", "part:m3"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_result_bs, _fmt_amount(result))

    # Dettes — bas:m50, part:m3, prd:m1
    ctx_debts = make_ctx([("dim:bas", "bas:m50"), ("dim:part", "part:m3"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_debts, _fmt_amount(debts))

    # Total passif — bas:m25, part:m3, prd:m1
    total_liabilities = equity + debts
    ctx_total_p = make_ctx([("dim:bas", "bas:m25"), ("dim:part", "part:m3"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_total_p, _fmt_amount(total_liabilities))

    # ─── INCOME STATEMENT (part:m4) ───

    # Cotisations, dons, legs, subsides — bas:m133, part:m4, prd:m1
    ctx_income = make_ctx([("dim:bas", "bas:m133"), ("dim:part", "part:m4"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_income, _fmt_amount(total_income))

    # Charges — bas:m136, part:m4, prd:m1
    ctx_expense = make_ctx([("dim:bas", "bas:m136"), ("dim:part", "part:m4"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am1", ctx_expense, _fmt_amount(total_expense))

    # Résultat de l'exercice — bas:m59, part:m4, prd:m1
    ctx_result = make_ctx([("dim:bas", "bas:m59"), ("dim:part", "part:m4"), ("dim:prd", "prd:m1")])
    _add_fact(root, "am2", ctx_result, _fmt_amount(result))

    # ─── IDENTIFICATION ───

    # Organization name — no dimensions needed, just entity+period
    ctx_name = make_ctx([])
    ns_met = NS["met"]
    name_fact = SubElement(root, f"{{{ns_met}}}str2", contextRef=ctx_name)
    name_fact.text = org.name

    # Serialize
    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes
