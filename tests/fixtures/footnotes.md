# Retinal Imaging Modalities

Optical coherence tomography (OCT) has revolutionized retinal diagnostics^[First commercialized by Carl Zeiss Meditec in 1996.] and remains the primary imaging modality for macular disease assessment.

## Spectral Domain OCT

SD-OCT provides axial resolution of approximately 5-7 µm[^1], enabling visualization of individual retinal layers. The technology uses a broadband light source and spectrometer[^resolution] to capture cross-sectional images.

Modern devices acquire 27,000-100,000 A-scans per second[^2], allowing dense volumetric scanning of the macula in under 3 seconds.

## OCT Angiography

OCTA uses the decorrelation signal between consecutive B-scans to map retinal vasculature without dye injection[^3]. This has largely replaced fluorescein angiography^[Though FA remains necessary for assessing leakage patterns and peripheral pathology.] for routine follow-up.

Key metrics include vessel density, foveal avascular zone area, and flow deficit mapping using `split-spectrum` amplitude decorrelation[^algo].

## Adaptive Optics

AO imaging achieves cellular-level resolution^[Resolving individual cone photoreceptors at ~2 µm spacing in the parafovea.] by correcting ocular aberrations in real time.

[^1]: Drexler W, Fujimoto JG. *Optical Coherence Tomography*. Springer, 2015.
[^resolution]: The spectral resolution determines the imaging depth range via $\Delta z = \frac{2\ln 2}{\pi} \cdot \frac{\lambda_0^2}{\Delta\lambda}$.
[^2]: Compared to ~400 A-scans/s for the original time-domain OCT systems.
[^3]: Spaide RF, Fujimoto JG, Waheed NK. "Image artifacts in OCT angiography." *Retina*. 2015;35(11):2163-80.
[^algo]: See the reference implementation at [GitHub](https://github.com/example/ssada-octa) for details.
