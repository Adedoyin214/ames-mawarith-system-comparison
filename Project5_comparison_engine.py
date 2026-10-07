"""
=============================================================
Mawārith Analytics — Project 5
Cross-System Comparative Analysis of Inheritance Distribution
=============================================================
Systems compared:
  1. Islamic (Fiqh al-Mawārith)     — Engine v2 (Hajb, Awl, Radd, Tanzeel)
  2. Nigerian Statutory             — Administration of Estates Law (AEL)
  3. Yoruba Customary               — Eldest-son primogeniture + others
  4. Igbo Customary                 — Male-lineage primacy
  5. Civil Equal-Share              — Neutral benchmark (equal per head)

Dataset     : 20 PCIED cases — PCIED 2023, Alhikma University, Ilorin
Institute   : Elbaseety Institute® | Mawārith Analytics
=============================================================
"""

from fractions import Fraction
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import sys, os, json, math, statistics as st
sys.path.insert(0, os.path.dirname(__file__))
from mawaarith_engine_v2 import MawaarithEngine, PCIED_CASES, Estate


# ─────────────────────────────────────────────
# SYSTEM DEFINITIONS
# ─────────────────────────────────────────────

SYSTEMS = ["Islamic", "Nigerian Statutory", "Yoruba Customary", "Igbo Customary", "Civil Equal-Share"]


# ─────────────────────────────────────────────
# 1. ISLAMIC — already handled by engine v2
# ─────────────────────────────────────────────

def compute_islamic(case: Estate, engine: MawaarithEngine) -> Dict[str, float]:
    r = engine.compute(case)
    out = {}
    for row in r.shares_table:
        if row["status"] == "Inherits" and row["share_fraction"] not in ("—", "0"):
            try:
                role = row["heir"].lower().replace(" ", "_")
                count = row["count"]
                pp = float(Fraction(row["share_per_person"]))
                for i in range(count):
                    out[f"{role}_{i+1}"] = pp * case.total_value
            except Exception:
                pass
    return out


# ─────────────────────────────────────────────
# 2. NIGERIAN STATUTORY — Administration of Estates Law
#    Rules (intestacy, no Will):
#    - Spouse:    1/3 of estate (if children exist), else 1/2
#    - Children:  share remaining 2/3 equally regardless of gender
#    - If no spouse: children share everything equally
#    - Parents:   inherit only if no spouse and no children
#    - Siblings:  inherit only if no spouse, children, or parents
# ─────────────────────────────────────────────

def compute_nigerian_statutory(case: Estate) -> Dict[str, float]:
    h = case.heirs_input
    total = case.total_value
    out = {}

    n_wives   = h.get("wife", 0)
    n_husband = h.get("husband", 0)
    n_spouse  = n_wives + n_husband
    n_sons    = h.get("son", 0)
    n_daughters = h.get("daughter", 0)
    n_children = n_sons + n_daughters
    n_father  = h.get("father", 0)
    n_mother  = h.get("mother", 0)
    n_parents = n_father + n_mother
    n_full_brothers = h.get("full_brother", 0)
    n_full_sisters  = h.get("full_sister", 0)
    n_siblings = n_full_brothers + n_full_sisters

    if n_children > 0:
        # Spouse gets 1/3, children share 2/3 equally
        spouse_total = Fraction(1, 3) if n_spouse > 0 else Fraction(0)
        child_total  = Fraction(1) - spouse_total

        if n_spouse > 0:
            sp_pp = float(spouse_total / n_spouse) * total
            role = "wife" if n_wives > 0 else "husband"
            for i in range(n_spouse):
                out[f"{role}_{i+1}"] = sp_pp

        child_pp = float(child_total / n_children) * total
        for i in range(n_sons):
            out[f"son_{i+1}"] = child_pp
        for i in range(n_daughters):
            out[f"daughter_{i+1}"] = child_pp

    elif n_spouse > 0:
        # No children — spouse gets 1/2, rest to parents if any else siblings
        spouse_total = Fraction(1, 2)
        sp_pp = float(spouse_total / n_spouse) * total
        role = "wife" if n_wives > 0 else "husband"
        for i in range(n_spouse):
            out[f"{role}_{i+1}"] = sp_pp

        remainder = Fraction(1, 2)
        if n_parents > 0:
            parent_pp = float(remainder / n_parents) * total
            for i in range(n_father):
                out[f"father_{i+1}"] = parent_pp
            for i in range(n_mother):
                out[f"mother_{i+1}"] = parent_pp
        elif n_siblings > 0:
            sib_pp = float(remainder / n_siblings) * total
            for i in range(n_full_brothers):
                out[f"full_brother_{i+1}"] = sib_pp
            for i in range(n_full_sisters):
                out[f"full_sister_{i+1}"] = sib_pp
        else:
            # No one to take remainder — reverts to spouse
            for k in out:
                out[k] += float(remainder / n_spouse) * total

    elif n_parents > 0:
        parent_pp = total / n_parents
        for i in range(n_father):
            out[f"father_{i+1}"] = parent_pp
        for i in range(n_mother):
            out[f"mother_{i+1}"] = parent_pp

    elif n_siblings > 0:
        sib_pp = total / n_siblings
        for i in range(n_full_brothers):
            out[f"full_brother_{i+1}"] = sib_pp
        for i in range(n_full_sisters):
            out[f"full_sister_{i+1}"] = sib_pp

    return out


# ─────────────────────────────────────────────
# 3. YORUBA CUSTOMARY LAW
#    - Eldest son (Dawodu) receives largest share (~double others)
#    - Remaining sons share balance equally
#    - Daughters receive ~half of each son's share
#    - Wife/wives receive usufruct only (no ownership) → modelled as 10% each
#    - Father/brothers may receive residue if no sons
#    Sources: Customary Law in Nigeria (Nwogugu 2014), Esan v Esan
# ─────────────────────────────────────────────

def compute_yoruba_customary(case: Estate) -> Dict[str, float]:
    h = case.heirs_input
    total = case.total_value
    out = {}

    n_sons    = h.get("son", 0)
    n_daughters = h.get("daughter", 0)
    n_wives   = h.get("wife", 0)
    n_husband = h.get("husband", 0)
    n_brothers= h.get("full_brother", 0)
    n_father  = h.get("father", 0)
    n_mother  = h.get("mother", 0)

    # Wives/husband: usufruct right ~10% each, capped at 30% total
    spouse_pool = 0.0
    if n_wives > 0:
        pp = min(0.10, 0.30 / n_wives) * total
        for i in range(n_wives):
            out[f"wife_{i+1}"] = pp
        spouse_pool = pp * n_wives
    if n_husband > 0:
        out["husband_1"] = 0.10 * total
        spouse_pool += 0.10 * total

    residue = total - spouse_pool

    if n_sons > 0:
        # Eldest son gets double unit; daughters get half unit each
        units = 2 + (n_sons - 1) + n_daughters * 0.5
        unit_val = residue / units
        out["son_1"] = 2 * unit_val          # eldest son (Dawodu)
        for i in range(1, n_sons):
            out[f"son_{i+1}"] = unit_val
        for i in range(n_daughters):
            out[f"daughter_{i+1}"] = 0.5 * unit_val

    elif n_daughters > 0:
        # No sons — daughters share equally
        dp = residue / n_daughters
        for i in range(n_daughters):
            out[f"daughter_{i+1}"] = dp

    elif n_brothers > 0:
        bp = residue / n_brothers
        for i in range(n_brothers):
            out[f"full_brother_{i+1}"] = bp

    elif n_father > 0:
        out["father_1"] = residue

    elif n_mother > 0:
        out["mother_1"] = residue

    return out


# ─────────────────────────────────────────────
# 4. IGBO CUSTOMARY LAW
#    - Sons inherit everything equally (agnatic primogeniture softened)
#    - First son (Okpara) gets compound house + larger share (~1.5x)
#    - Daughters inherit nothing from father's estate (movables only, sometimes)
#      → modelled as daughters get 0 from estate (traditional strict rule)
#    - Wife has right of occupancy only (no ownership)
#    - Sources: Nezianya v Okagbue (1963), Chinweze v Masi (1989)
# ─────────────────────────────────────────────

def compute_igbo_customary(case: Estate) -> Dict[str, float]:
    h = case.heirs_input
    total = case.total_value
    out = {}

    n_sons    = h.get("son", 0)
    n_daughters = h.get("daughter", 0)
    n_wives   = h.get("wife", 0)
    n_brothers= h.get("full_brother", 0)
    n_father  = h.get("father", 0)
    n_uncle   = h.get("full_uncle", 0) + h.get("paternal_uncle", 0)

    # Wives: maintenance right only (~5% each, no ownership)
    if n_wives > 0:
        pp = min(0.05, 0.15 / n_wives) * total
        for i in range(n_wives):
            out[f"wife_{i+1}"] = pp
        spouse_pool = pp * n_wives
    else:
        spouse_pool = 0.0

    residue = total - spouse_pool

    if n_sons > 0:
        # First son (Okpara) gets 1.5 units; others 1 unit each; daughters 0
        units = 1.5 + (n_sons - 1)
        unit_val = residue / units
        out["son_1"] = 1.5 * unit_val     # Okpara
        for i in range(1, n_sons):
            out[f"son_{i+1}"] = unit_val
        # Daughters: traditionally 0 from landed estate
        for i in range(n_daughters):
            out[f"daughter_{i+1}"] = 0.0

    elif n_brothers > 0:
        # No sons — brothers of deceased (agnates) share
        bp = residue / n_brothers
        for i in range(n_brothers):
            out[f"full_brother_{i+1}"] = bp

    elif n_father > 0:
        out["father_1"] = residue

    elif n_uncle > 0:
        up = residue / n_uncle
        for i in range(n_uncle):
            out[f"uncle_{i+1}"] = up

    return out


# ─────────────────────────────────────────────
# 5. CIVIL EQUAL-SHARE (neutral benchmark)
#    Every listed heir gets equal share regardless of role
# ─────────────────────────────────────────────

def compute_civil_equal(case: Estate) -> Dict[str, float]:
    h = case.heirs_input
    total = case.total_value
    all_heirs = sum(h.values())
    if all_heirs == 0:
        return {}
    pp = total / all_heirs
    out = {}
    for role, count in h.items():
        for i in range(count):
            out[f"{role}_{i+1}"] = pp
    return out


# ─────────────────────────────────────────────
# GINI HELPER
# ─────────────────────────────────────────────

def gini(values: List[float]) -> float:
    vals = sorted([v for v in values if v > 0])
    if not vals or len(vals) == 1:
        return 0.0
    n = len(vals)
    cumsum = sum((2*(i+1) - n - 1) * v for i, v in enumerate(vals))
    return cumsum / (n * sum(vals))


# ─────────────────────────────────────────────
# SUMMARY METRICS PER SYSTEM
# ─────────────────────────────────────────────

@dataclass
class SystemResult:
    system: str
    shares: Dict[str, float]    # heir_key -> naira amount
    total_assigned: float
    gini: float
    n_heirs_receiving: int
    coverage_rate: float        # % of all heirs who receive something

    def per_person_list(self) -> List[float]:
        return [v for v in self.shares.values() if v > 0]


@dataclass
class CaseComparison:
    case_id: int
    name: str
    location: str
    total_value: int
    heirs_input: Dict[str, int]
    systems: Dict[str, SystemResult]


# ─────────────────────────────────────────────
# MAIN COMPARISON ENGINE
# ─────────────────────────────────────────────

def compare_all_cases() -> List[CaseComparison]:
    engine = MawaarithEngine()
    results = []

    for i, case in enumerate(PCIED_CASES, 1):
        n_total_heirs = sum(case.heirs_input.values())

        system_fns = {
            "Islamic":            lambda c: compute_islamic(c, engine),
            "Nigerian Statutory": compute_nigerian_statutory,
            "Yoruba Customary":   compute_yoruba_customary,
            "Igbo Customary":     compute_igbo_customary,
            "Civil Equal-Share":  compute_civil_equal,
        }

        sys_results = {}
        for sys_name, fn in system_fns.items():
            shares = fn(case)
            assigned = sum(shares.values())
            n_recv = sum(1 for v in shares.values() if v > 0)
            coverage = n_recv / n_total_heirs if n_total_heirs > 0 else 0
            g = gini(list(shares.values()))
            sys_results[sys_name] = SystemResult(
                system=sys_name,
                shares=shares,
                total_assigned=round(assigned, 2),
                gini=round(g, 4),
                n_heirs_receiving=n_recv,
                coverage_rate=round(coverage * 100, 1),
            )

        results.append(CaseComparison(
            case_id=i,
            name=case.deceased_name,
            location=case.location,
            total_value=case.total_value,
            heirs_input=case.heirs_input,
            systems=sys_results,
        ))

    return results


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  MAWĀRITH ANALYTICS — Project 5: Cross-System Comparison")
    print("=" * 70)

    comparisons = compare_all_cases()

    # Header
    print(f"\n  {'Case':>3}  {'System':<22} {'Total Assigned':>16} {'Gini':>7} {'N Recv':>7} {'Cover%':>7}")
    print(f"  {'-'*68}")

    for comp in comparisons:
        first = True
        for sys_name, r in comp.systems.items():
            label = f"[{comp.case_id}]" if first else "   "
            print(f"  {label:>3}  {sys_name:<22} ₦{r.total_assigned:>14,.0f} {r.gini:>7.4f} {r.n_heirs_receiving:>7} {r.coverage_rate:>6.1f}%")
            first = False
        print()

    # Aggregate stats
    print(f"\n  AGGREGATE — MEAN GINI ACROSS ALL 20 CASES")
    print(f"  {'-'*50}")
    for sys_name in SYSTEMS:
        ginis = [c.systems[sys_name].gini for c in comparisons if sys_name in c.systems]
        coverage = [c.systems[sys_name].coverage_rate for c in comparisons if sys_name in c.systems]
        print(f"  {sys_name:<26} Gini={st.mean(ginis):.4f}  Coverage={st.mean(coverage):.1f}%")

    # Save JSON
    export = []
    for comp in comparisons:
        export.append({
            "case_id": comp.case_id,
            "name": comp.name,
            "location": comp.location,
            "total_value": comp.total_value,
            "heirs_input": comp.heirs_input,
            "systems": {
                sys_name: {
                    "shares": {k: round(v, 2) for k, v in r.shares.items()},
                    "total_assigned": r.total_assigned,
                    "gini": r.gini,
                    "n_heirs_receiving": r.n_heirs_receiving,
                    "coverage_rate": r.coverage_rate,
                }
                for sys_name, r in comp.systems.items()
            }
        })

    with open(os.path.join(os.path.dirname(__file__), "comparison_results.json"), "w") as f:
        json.dump(export, f)

    print(f"\n  Saved → comparison_results.json")
    print(f"{'='*70}")
