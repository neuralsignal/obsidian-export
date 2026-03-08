# Clinical Trial Summary

## Study Design

### Phase III Randomized Controlled Trial

#### Primary Endpoints

The study measured **visual acuity** at 12 months using *ETDRS charts*. Patients with ~~poor compliance~~ irregular follow-up were excluded.

---

Key inclusion criteria:

1. Age 50-85 years
2. Confirmed diagnosis of nAMD
   1. Active CNV on OCT
   2. Lesion size < 12 disc areas
3. BCVA between 25 and 75 letters

Surgical approaches considered:

- Intravitreal injection
- Subretinal delivery
  - Via pars plana vitrectomy
  - Via suprachoroidal access
- Topical (experimental)

> The treat-and-extend protocol has become the standard of care for anti-VEGF therapy in most retina clinics worldwide.

### Code Examples

```python
def calculate_injection_interval(response: str) -> int:
    """Determine next injection interval in weeks."""
    if response == "dry":
        return min(current_interval + 2, 16)
    return max(current_interval - 2, 4)
```

```bash
# Export patient data for analysis
pixi run python scripts/export_cohort.py --study-id NCT04123456
```

Use `oct_analyzer.segment()` to process B-scans automatically.

### Outcome Measures

The mean change in BCVA was $+8.2$ letters (95% CI: $+6.1$ to $+10.3$).

The treatment effect can be modeled as:

$$
\Delta V = \beta_0 + \beta_1 T + \beta_2 \log(\text{CST}_0) + \epsilon
$$

### Task Checklist

- [x] IRB approval obtained
- [x] Patient recruitment completed
- [ ] 12-month follow-up data collected
- [ ] Statistical analysis finalized
- [ ] Manuscript submitted
