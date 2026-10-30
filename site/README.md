# Tender Academy Teaching Site

Static bilingual course for GitHub Pages and the local application.

## Local preview

```bash
python -m http.server 8090 --directory site
```

Open <http://127.0.0.1:8090/>.

The application also mounts the site at `/guide/` when running FastAPI.

## Features

- eight bilingual modules;
- local learning progress;
- language switch;
- knowledge checks;
- formula and evidence-boundary cards;
- printable course;
- no external CDN, tracking or runtime dependency.

## GitHub Pages

`.github/workflows/pages.yml` deploys this directory whenever `site/` changes on
`main`. In repository settings, Pages must use GitHub Actions as its source.
