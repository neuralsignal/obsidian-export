# Troubleshooting — OCT Acquisition

> [!warning] Poor Signal Quality
> If signal strength is below 6/10, check the following before repeating the scan:
>
> 1. Clean the chin rest and forehead bar
> 2. Verify tear film — instill artificial tears if needed
> 3. Re-align the pupil using the IR preview
> 4. Reduce room lighting
>
> | Cause | Signal Impact | Fix |
> |-------|--------------|-----|
> | Dry cornea | Moderate | Artificial tears |
> | Small pupil | Severe | Dilate or use small-pupil mode |
> | Media opacity | Variable | Adjust focus + enhance |

> [!tip] Segmentation Artifacts
> When automated segmentation fails at the foveal pit, use manual correction:
>
> ```python
> from oct_tools import correct_segmentation
>
> corrected = correct_segmentation(
>     bscan=scan_data,
>     layer="ILM",
>     method="spline",
>     anchor_points=[(128, 45), (256, 42), (384, 47)]
> )
> ```
>
> Save corrected scans with the `_manual` suffix for audit trail.

> [!danger] Critical — Injection Complications
> If endophthalmitis is suspected:
>
> > [!important] Immediate Steps
> > 1. Obtain vitreous tap and culture
> > 2. Intravitreal antibiotics (vancomycin 1 mg + ceftazidime 2.25 mg)
> > 3. Urgent retina consultation
>
> Do **not** delay treatment for imaging. Time to treatment is the strongest prognostic factor.

> [!note] Documentation Requirements
> All adverse events must be recorded in the electronic health record within 24 hours using the standardized form under `Reports → Adverse Events → Intravitreal`.
