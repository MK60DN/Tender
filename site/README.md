# Tender Academy Teaching Site

Static bilingual course for the Tender repository.

- Eight modules with Chinese and English versions
- Local progress storage
- Knowledge checks
- Printable lessons
- No mathematical formulas or derivations
- No external CDN, tracking or runtime dependency

## Local preview

```bash
python -m http.server 8090 --directory site
```

Open <http://127.0.0.1:8090/>.

## GitHub Pages

The deployment workflow is `.github/workflows/pages.yml`. The repository owner must enable GitHub Pages with **GitHub Actions** as the source once under repository Settings → Pages. After that, updates under `site/` deploy automatically.
