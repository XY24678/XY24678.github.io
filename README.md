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

The site uses relative internal URLs and can run under a GitHub Pages project subpath. No Git repository, remote, deployment, or GitHub Pages configuration has been created.

## Pending real assets

- One user-provided lifestyle photo in a 4:5 crop
- A Chinese PDF resume, if the Chinese page should offer a language-matched download
