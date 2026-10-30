# Publish to GitHub

The prepared repository is a clean, standalone Git history. The existing remote
repository is `https://github.com/MK60DN/Tender.git`.

## Recommended: push to a release branch first

From this directory:

```bash
git fetch origin
git push origin HEAD:release/v1.6.1
git push origin v1.6.1
```

Then open a pull request from `release/v1.6.1` to `main`, review the full diff,
and merge when satisfied.

## Replace main directly

Only use this after reviewing the diff and confirming that all previous remote
content may be replaced:

```bash
git fetch origin
git push --force-with-lease origin HEAD:main
git push origin v1.6.1
```

This is a destructive history replacement. The recommended branch workflow is
safer.

## Restore from bundle

```bash
git clone Tender-v1.6.1.bundle Tender
cd Tender
git remote set-url origin https://github.com/MK60DN/Tender.git
```
