# Publish to GitHub

The prepared repository is a clean, standalone Git history. The existing remote
repository is `https://github.com/MK60DN/Tender.git`.

## Recommended path

From this directory:

```bash
git fetch origin
git rebase origin/main
git push origin main
git push origin v1.9.0
```

The release should be a fast-forward on the existing remote history. Do not
replace or truncate remote history.

## Restore from bundle

```bash
git clone Tender-v1.9.0.bundle Tender
cd Tender
git remote set-url origin https://github.com/MK60DN/Tender.git
```
