# Releasing

For maintainers: how a version gets to PyPI. A release is a pushed `v*` tag plus one approval; `.github/workflows/release.yml` does the rest. Decision record: [ADR-0025](../adr/0025-version-from-the-git-tag-and-release-to-pypi-on-tag-push.md).

## One-time setup

1. On [PyPI](https://pypi.org/manage/account/publishing/) and [TestPyPI](https://test.pypi.org/manage/account/publishing/), add a pending trusted publisher (the project doesn't exist there until the first upload):

   | Field             | PyPI         | TestPyPI     |
   | ----------------- | ------------ | ------------ |
   | PyPI project name | `citefield`  | `citefield`  |
   | Owner             | `aleche28`   | `aleche28`   |
   | Repository name   | `citefield`  | `citefield`  |
   | Workflow name     | `release.yml` | `release.yml` |
   | Environment name  | `pypi`       | `testpypi`   |

2. On GitHub, under Settings → Environments, create:
   - `pypi`, with yourself as a required reviewer, and deployment limited to tags matching `v*`.
   - `testpypi`, with no protection rules.
3. Optionally, add a tag ruleset for `v*` so that only maintainers can create, move or delete release tags.

## Check the pipeline on TestPyPI

Run the Release workflow by hand: Actions → Release → Run workflow, on `main`. It runs the checks, builds a dev version such as `0.1.dev44` and publishes it to TestPyPI. A second run on the same commit builds the same version, which is skipped. Then download the wheel from TestPyPI and install it, with the dependencies from PyPI only (anyone can upload to TestPyPI, so don't resolve dependencies there):

```sh
uvx pip download --no-deps --index-url https://test.pypi.org/simple/ \
  citefield==0.1.dev44 -d /tmp/citefield-testpypi
uv tool install /tmp/citefield-testpypi/citefield-0.1.dev44-py3-none-any.whl
citefield --version
uv tool uninstall citefield
```

## Cut a release

1. Make sure `main` is green and has everything the release should contain. The PR titles become the release notes, so they should read well.
2. Tag the commit with the version, `v` plus a [canonical version](https://packaging.python.org/en/latest/specifications/version-specifiers/), and push the tag:

   ```sh
   git switch main && git pull
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin v0.1.0
   ```

3. The workflow runs the checks and builds. Approve the `pypi` deployment when it asks, under the workflow run.
4. Check the [PyPI page](https://pypi.org/p/citefield), the GitHub Release and `uv tool install citefield`.

SemVer 0.x applies: bump the minor version for anything that breaks the output JSON, signals, config schema, CLI or API, and the patch version otherwise.

## Pre-releases

Tag `v0.2.0rc1` (not `v0.2.0-rc1`, which isn't canonical and fails the version check). It goes to PyPI as a pre-release, which `pip` and `uv` only install when asked (`citefield==0.2.0rc1` or `--prerelease allow`), and the GitHub Release is marked as a pre-release.

## When a release fails

- **The checks or the version check fail:** nothing was published. Delete the tag, fix `main` and tag again:

  ```sh
  git push --delete origin v0.1.0 && git tag -d v0.1.0
  ```

- **The PyPI upload fails,** for example because the trusted publisher doesn't match: fix the publisher settings, then re-run the failed jobs of the same run. It publishes the files that were already built.
- **The GitHub Release fails after PyPI accepted the upload:** re-run that job only.
- **A broken version reached PyPI:** PyPI never accepts the same version twice, even after a delete. Yank it on PyPI (installs that pin it still work), fix `main` and release the next patch version.
