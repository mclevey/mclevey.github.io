# GitHub API Caching and Enhanced Data Fetching

## Context

In `scripts/build_cv.py`, there's a function `fetch_github_info()` that fetches version and commit info from the GitHub API for software packages listed in `records/cv.md`. Currently it has issues:

1. No caching - hits the API every build, causing rate limiting
2. Falls back to "XX.XX" placeholders when rate limited
3. Only fetches basic info (version, last commit date, commit SHA)

## Task

Refactor the `fetch_github_info()` function and add a caching system with these requirements:

### 1. Cache File System

Create a JSON cache file at `records/github_cache.json` that stores fetched data for each repository. Structure:

```json
{
  "mclevey/dcss": {
    "last_fetched": "2024-01-15T10:30:00Z",
    "version": "v1.2.3",
    "last_commit_date": "2024-01-10",
    "last_commit_sha": "abc1234",
    "first_commit_date": "2020-03-15",
    "total_commits": 547,
    "contributors": ["mclevey", "contributor1", "contributor2"],
    "contributor_count": 3,
    "open_issues": 5,
    "stars": 42,
    "forks": 8,
    "description": "Repository description from GitHub",
    "topics": ["python", "data-science"],
    "license_spdx": "MIT",
    "created_at": "2020-03-15T00:00:00Z",
    "updated_at": "2024-01-10T00:00:00Z"
  }
}
```

### 2. Cache Freshness Logic

- If cache entry exists and `last_fetched` is within 15 minutes, use cached data
- If cache is stale (>15 minutes), fetch fresh data from API
- If YAML has `force-api-call: true` for a package, always fetch fresh data
- If rate limited (HTTP 403 with "rate limit" in response), use cached data instead of placeholders
- Print clear messages about cache status: "Using cached data for X (Y minutes old)" or "Fetching fresh data for X"

### 3. Enhanced GitHub API Data

Fetch all available useful information from these endpoints:

**Repository info** (`/repos/{owner}/{repo}`):

- `stargazers_count` → stars
- `forks_count` → forks
- `open_issues_count` → open_issues
- `description` → description
- `topics` → topics
- `license.spdx_id` → license_spdx
- `created_at` → created_at
- `updated_at` → updated_at

**Latest release** (`/repos/{owner}/{repo}/releases/latest`):

- `tag_name` → version

**Tags** (`/repos/{owner}/{repo}/tags`) - fallback if no releases:

- First tag name → version

**Commits** (`/repos/{owner}/{repo}/commits`):

- First commit → last_commit_date, last_commit_sha
- Need to paginate to get first commit (or use `?per_page=1&page=<last>`)

**Commit count** - Use the commits endpoint with `per_page=1` and check the `Link` header for total pages, or use:

```
/repos/{owner}/{repo}/commits?per_page=1
```

Then parse the `Link` header to get total count.

**Contributors** (`/repos/{owner}/{repo}/contributors`):

- Extract login names → contributors list
- Length → contributor_count

### 4. Return Structure

The `fetch_github_info()` function should return a dict with all these fields:

```python
{
    "version": "v1.2.3",           # From releases/tags, or YAML fallback, or "XX.XX"
    "last_commit_date": "2024-01-10",
    "last_commit_sha": "abc1234",   # Short SHA (7 chars)
    "first_commit_date": "2020-03-15",
    "total_commits": 547,
    "contributors": ["user1", "user2"],
    "contributor_count": 3,
    "open_issues": 5,
    "stars": 42,
    "forks": 8,
    "description": "...",
    "topics": ["python", "ml"],
    "license_spdx": "MIT",
    "created_at": "2020-03-15",
    "updated_at": "2024-01-10",
    "from_cache": True,             # Boolean indicating if data came from cache
    "cache_age_minutes": 12,        # How old the cache is (if from cache)
}
```

### 5. Fallback Priority

For each field, use this priority:

1. Fresh GitHub API data (if available and not rate limited)
2. Cached data from `github_cache.json`
3. YAML data from cv.md (e.g., `version`, `last_commit`, `commit_id` fields)
4. Placeholder values ("XX.XX", "XXXX-XX-XX", "XXXXXXX", 0, [], etc.)

### 6. Rate Limit Handling

- Check response headers for `X-RateLimit-Remaining`
- If remaining is 0 or get 403 response, print warning and use cache
- Print current rate limit status at start: "GitHub API: X/60 requests remaining"

### 7. Error Handling

- Print clear warnings for each type of error
- Never crash the build - always fall back gracefully
- Log which data came from cache vs fresh fetch

### 8. Code Organization

Create these helper functions:

- `load_github_cache()` - Load cache file, return empty dict if doesn't exist
- `save_github_cache(cache)` - Save cache to file
- `is_cache_fresh(cache_entry, max_age_minutes=15)` - Check if entry is fresh
- `fetch_repo_info(owner, repo)` - Fetch from /repos endpoint
- `fetch_commits_info(owner, repo)` - Fetch commit data
- `fetch_contributors(owner, repo)` - Fetch contributor list
- `fetch_github_info(github_url, yaml_data=None, force_refresh=False)` - Main function

### 9. Software Section Variables

In the software section loop, make all these variables available for templating:

```python
# Basic info
package = "dcss"
github_url = "https://github.com/mclevey/dcss"
description = "..."
team = "John McLevey, ..."
license_text = "MIT License"
language = "Python"

# From GitHub API / cache
version = "v1.2.3"
last_commit_date = "2024-01-10"
last_commit_sha = "abc1234"
first_commit_date = "2020-03-15"
total_commits = 547
contributors = ["mclevey", "user2"]
contributor_count = 3
open_issues = 5
stars = 42
forks = 8
repo_description = "..."
topics = ["python", "data-science"]
license_spdx = "MIT"
created_at = "2020-03-15"
updated_at = "2024-01-10"
from_cache = True
cache_age_minutes = 12
```

### 10. Testing

After implementation:

1. Run build twice quickly - second should use cache
2. Wait 16 minutes, run again - should fetch fresh
3. Add `force-api-call: true` to one package in cv.md - should always fetch
4. Disconnect internet and run - should use cache gracefully
5. Check github_cache.json is created and properly formatted

### 11. Example YAML with force flag

```yaml
software:
  - package: dcss
    license: GNU GPL2
    github: https://github.com/mclevey/dcss
    force-api-call: true # Always fetch fresh data for this package
    # Optional manual overrides (used as fallback):
    version: "1.0.0"
    last_commit: "2024-01-15"
    commit_id: "abc1234"
    description: "..."
    development: "John McLevey, Tyler Crick, Pierson Browne"
```

## Files to Modify

1. `scripts/build_cv.py` - Main implementation
2. `records/github_cache.json` - Will be created automatically (add to .gitignore if desired)

## Additional Notes

- Use `urllib.request` (already imported) - no external dependencies
- Respect GitHub's rate limit of 60 requests/hour for unauthenticated requests
- The cache file should be human-readable (use `indent=2` in json.dump)
- Print a summary at the end: "GitHub data: X packages fetched fresh, Y from cache"
