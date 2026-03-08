# Reference Links and URLs

## Clinical Trial Databases

Short URL: https://clinicaltrials.gov

Long registration URL: https://clinicaltrials.gov/ct2/show/NCT04123456?term=anti-vegf&cond=Age-Related+Macular+Degeneration&phase=2&draw=2&rank=1

Named link: [ClinicalTrials.gov Registry](https://clinicaltrials.gov/ct2/show/NCT04123456?term=anti-vegf&cond=Age-Related+Macular+Degeneration)

## Journal References

- [HARBOR Study Results](https://www.nejm.org/doi/full/10.1056/NEJMoa1310461?query=featured_retina&utm_source=newsletter&utm_medium=email)
- [CATT Trial 5-Year Outcomes](https://jamanetwork.com/journals/jamaophthalmology/fullarticle/2587171?resultClick=1&campaign=retina-quarterly)
- Simple DOI: https://doi.org/10.1001/jamaophthalmol.2024.0012

## URLs in Code Context

```python
API_BASE = "https://api.openalex.org/works"
SEARCH_URL = (
    "https://api.openalex.org/works?filter=concepts.id:C121332964,"
    "publication_year:2024&sort=cited_by_count:desc&per_page=50"
)
response = requests.get(f"{API_BASE}?search={query}&mailto=user@example.com")
```

## Bare URLs in Text

The EURETINA guidelines are available at https://www.euretina.org/guidelines/ and the SOG-SSO recommendations at https://www.sog-sso.ch/fileadmin/user_upload/sog-sso/pdf/Richtlinien_Guidelines/2024_Anti-VEGF_Empfehlungen_DE.pdf for Swiss-specific protocols.

## Internal Vault Links

See also [[Clinical Protocols]] and [[Anti-VEGF Dosing Guide#Treat and Extend]].
