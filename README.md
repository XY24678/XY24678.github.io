# XI YU Resume-first Portfolio

Buildless bilingual static site with an online resume and a separate project index. No package installation is required.

## Public pages

- English resume: `/index.html`
- English projects: `/projects/`
- Chinese resume: `/zh/`
- Chinese projects: `/zh/projects/`

The former long-form case-study pages have been retired. Project entries link directly to the real public products.

## Local preview

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/` for the English resume or `http://localhost:8000/zh/` for the Chinese resume.

## Validation

```powershell
python -m unittest discover -s tests -v
```

The site uses relative internal URLs and is published from the `main` branch with GitHub Pages at [xy24678.github.io](https://xy24678.github.io/).

## Current assets

- User-provided lifestyle photo, cropped and optimized for the web
- English PDF resume linked from both language versions
