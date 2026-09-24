# Releasing a new version to PyPI

Releases are built and uploaded by GitHub Actions (`.github/workflows/python-publish-pypi.yml`)
using PyPI *trusted publishing*, so no API token is stored anywhere. Pushing a tag
`vX.Y.Z` is the trigger. The workflow:

1. runs the CI checks (ruff, pytest on Python 3.9–3.13, build check),
2. verifies that the tag matches `__version__` and that `CHANGELOG.md` has a section for it,
3. builds the sdist and wheel and runs `twine check`,
4. uploads to PyPI (environment `pypi`),
5. creates a GitHub release with the built files attached and auto-generated notes.

## One-time setup (already done for this repository; repeat only for a fork)

1. **PyPI trusted publisher.** On <https://pypi.org/manage/project/planta-filler/settings/publishing/>
   add a GitHub publisher with owner `d-solve-de`, repository `planta-automation`,
   workflow `python-publish-pypi.yml`, environment `pypi`.
   For a brand-new project use the "pending publisher" form at
   <https://pypi.org/manage/account/publishing/> instead; the first upload then creates the project.
2. **GitHub environment.** In the repository settings → *Environments* create `pypi`.
   Optionally add yourself as a required reviewer so every upload needs a click.
   Create `testpypi` the same way if you want to use TestPyPI (add the trusted
   publisher on <https://test.pypi.org/> with environment `testpypi`).
3. Nothing else: the workflow requests an OIDC token (`id-token: write`) and PyPI
   accepts it because of step 1.

## Release checklist

```bash
git checkout main && git pull
make check                                 # everything green locally
```

1. **Pick the version.** Semantic versioning: `MAJOR.MINOR.PATCH`.
   Bug fixes → patch, new options or behaviour → minor, breaking CLI changes → major.
2. **Set the version** in exactly one place: `src/planta_filler/__init__.py`
   ```python
   __version__ = "0.3.0"
   ```
   `pyproject.toml` reads it dynamically; do not edit a version there.
3. **Update `CHANGELOG.md`:** rename `[Unreleased]` to `[0.3.0] - YYYY-MM-DD`, add a fresh
   empty `[Unreleased]` above it and update the compare links at the bottom.
4. **Commit and push:**
   ```bash
   git commit -am "Release 0.3.0"
   git push origin main
   ```
   Wait for the CI workflow on `main` to pass.
5. **Tag and push the tag** (this triggers the publish workflow):
   ```bash
   git tag -a v0.3.0 -m "planta-filler 0.3.0"
   make release-check          # tag on HEAD == v<__version__> and CHANGELOG has the section
   git push origin v0.3.0
   ```
6. **Watch the workflow** under *Actions → Publish to PyPI*. If you configured a
   required reviewer on the `pypi` environment, approve the deployment there.
7. **Verify:**
   ```bash
   pip3 install --upgrade planta-filler
   planta-filler --version      # prints 0.3.0
   ```
   Check <https://pypi.org/project/planta-filler/> and the GitHub release page.

## Dry run on TestPyPI

Before a risky release, publish to TestPyPI from any branch without tagging:
*Actions → Publish to PyPI → Run workflow → target: testpypi*. Then:

```bash
pip3 install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ planta-filler==0.3.0
```

TestPyPI refuses to re-upload the same version; bump the version (or use a
`.devN` suffix like `0.3.0.dev1`) to try again. The workflow passes
`skip-existing: true` for TestPyPI so a repeated run does not fail.

## Manual upload (fallback when Actions is unavailable)

You need a PyPI API token (<https://pypi.org/manage/account/token/>) scoped to the project.

```bash
make build                                   # dist/planta_filler-X.Y.Z*.whl and .tar.gz
python3 -m twine upload dist/*               # username: __token__, password: the token
```

Set `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=pypi-...` to avoid the prompt.
Afterwards still push the tag so the repository and the GitHub release stay in sync.

## Fixing a broken release

PyPI never allows re-uploading a version. Bump the patch version, fix, and release
again. If a release must not be installed, *yank* it on PyPI (project → releases →
options); yanked versions are skipped by `pip install planta-filler` but remain
installable when pinned explicitly.

## What the version check enforces

The `build` job fails if:

- the tag `vX.Y.Z` does not equal `__version__` (typo in one of them), or
- `CHANGELOG.md` has no `## [X.Y.Z]` heading.

Fix the mistake, move the tag (`git tag -f vX.Y.Z && git push -f origin vX.Y.Z`) and
the workflow runs again. Nothing was uploaded, so this is safe.
