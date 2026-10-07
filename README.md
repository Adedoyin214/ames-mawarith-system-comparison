# AMES Mawārith System Comparison — Islamic vs. Nigerian Statutory vs. Customary Inheritance

**Project 5 of AMES (Algorithmic Mawārith Execution System)** — runs the same 20 real estates through five different inheritance systems and compares who gets what: Islamic (Fiqh al-Mawārith), Nigerian statutory law, Yoruba customary law, Igbo customary law, and a neutral civil equal-share benchmark.

## The five systems

| System | Key rules as modelled |
|---|---|
| **Islamic** | Fixed Qur'anic shares (1/2, 1/3, 1/4, 1/6, 1/8, 2/3), residue to ʿaṣaba, 'Awl and Radd to keep the sum at 1, Tanzeel for distant kindred |
| **Nigerian Statutory** | Administration of Estates Law: spouse gets 1/3 (children present) or 1/2; children share the rest equally regardless of gender |
| **Yoruba Customary** | Eldest-son primogeniture (Dawodu): eldest son double share, daughters half a son's unit, wife usufruct only (~10%) |
| **Igbo Customary** | Male-line primacy (Okpara): first son 1.5×, daughters nothing from landed estate, wife maintenance only (~5%) |
| **Civil Equal-Share** | Every listed heir gets exactly 1/N — Gini = 0 by construction |

These are simplified models of each system for comparison purposes, not legal advice.

## What it measures

For each of the 20 PCIED cases and each system: **Gini coefficient** (inequality among recipients), **coverage** (share of listed heirs who receive anything), and **estate distributed** (share of the estate actually assigned).

## Results (20 PCIED cases)

| System | Mean Gini | Mean coverage | Mean estate distributed |
|---|:---:|:---:|:---:|
| Islamic | 0.2295 | 69.3% | 100% |
| Nigerian Statutory | 0.0945 | 37.1% | 90.0% |
| Yoruba Customary | 0.1902 | 38.2% | 82.5% |
| Igbo Customary | 0.0798 | 20.6% | 47.5% |
| Civil Equal-Share | 0.0000 | 100% | 100% |

- **Higher Gini is not "worse" here.** Islamic law has the highest Gini because it differentiates between the most heir types, while distributing 100% of every estate.
- **Igbo customary's low Gini is misleading.** It reflects sameness among the very few people who receive anything (20.6% coverage), not fairness.
- **Cases 13 and 14 expose a gap.** Where all heirs are distant relatives (e.g. daughter's son, paternal aunt), the statutory and both customary models assign ₦0; only Islamic (via Tanzeel) and the civil benchmark distribute the estate.
- **Daughters:** in the cases where daughters are present, their mean group share is 55.6% (Islamic), 60.3% (Statutory), 71.8% (Yoruba), 33.6% (Civil), and 0% (Igbo). These are averages over different heir mixes, so they compare outcomes in this dataset, not per-heir rules.
- **Wives:** mean group share where a wife is present is 50.0% (Statutory), 22.0% (Civil), 20.0% (Yoruba), 17.9% (Islamic), 10.0% (Igbo). The Islamic share is a fixed entitlement (1/8 with children, 1/4 without) rather than a function of how many other heirs there are.

![Gini and coverage by system](images/Project5_fig1_gini_coverage.png)
![Gini heatmap, 5 systems x 20 cases](images/Project5_fig2_gini_heatmap.png)

## Contents

| File | Description |
|---|---|
| `Project5_comparison_engine.py` | Implements all five systems and runs the 20-case comparison |
| `mawaarith_engine_v2.py` | Fiqh al-Mawārith engine (shared across AMES) |
| `notebooks/Project5_Comparison.ipynb` | Aggregate metrics, system profiles, daughter-share table |
| `Project5_Dashboard.html` | Interactive dashboard |
| `images/` | Four comparison figures |
| `data/PCIED_2023_cases.md` | Source dataset (shared across AMES projects) |
| `reports/Project5_Comparison_Report.docx` | Full written report |

## Running it

```bash
python Project5_comparison_engine.py
```

Writes `comparison_results.json`, which the notebook reads.

## Author

Abdulbasit A. Adedeji (Data Ustadh)
