# GitHub Actions Status Badges

Add these badges to your README.md to show the status of your automated tests:

## DVC Pipeline Smoke Test
[![DVC Pipeline Smoke Test](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5/actions/workflows/dvc-smoke-test.yml/badge.svg)](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5/actions/workflows/dvc-smoke-test.yml)

## Usage in README.md
Copy and paste this into your main README.md file:

```markdown
![DVC Pipeline Test](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5/actions/workflows/dvc-smoke-test.yml/badge.svg)
```

## What This Shows
- ✅ Green badge: All tests passing, PR ready to merge
- ❌ Red badge: Tests failing, needs attention  
- 🟡 Yellow badge: Tests running or pending

The badge automatically updates when:
- New commits are pushed to main branch
- Pull requests are opened or updated
- Scheduled workflow runs execute