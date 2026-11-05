# 0025. Take the version from the git tag, and release to PyPI when a tag is pushed

- Status: Accepted
- Date: 2026-11-05

## Context

citefield had no way to ship: the version was a hand-kept `0.0.1`, nothing was on PyPI and no workflow released it. The first release, 0.1.0, needs a version scheme and a release path that are safe to run by one maintainer, and the README is already written to be the PyPI page. Decided in issue [#20](https://github.com/aleche28/citefield/issues/20). See [design.md, Releases](../design.md#releases).

## Considered options

- **Version from the git tag, with hatch-vcs**: tag `v0.2.0` gives 0.2.0, no bump commits, and builds between tags get a dev version. Adds hatch-vcs (MIT) as a build requirement, and builds need the git history and tags.
- **Version in `pyproject.toml`, bumped by hand or a tool**: no new build dependency, but every release needs a bump commit that has to agree with the tag.

For publishing, the alternative to Trusted Publishing is a PyPI API token stored as a secret, which lasts until revoked and can leak.

## Decision

We will take the version from the git tag with hatch-vcs, using SemVer 0.x, so a minor version may break things.

Pushing a `v*` tag starts `.github/workflows/release.yml`. It runs the full CI first (`ci.yml` through `workflow_call`), checks that the built files carry the tag's version, builds the sdist and wheel once and publishes exactly those files to PyPI with Trusted Publishing (OIDC, no tokens). Publishing runs in a `pypi` GitHub environment that needs a maintainer's approval. The workflow then creates the GitHub Release with GitHub's generated notes and the files attached. There is no `CHANGELOG.md`.

`rc` tags, such as `v0.2.0rc1`, go to PyPI as pre-releases and are marked as pre-releases on GitHub. Running the workflow by hand publishes the current dev build to TestPyPI instead, to check the pipeline. Builds between tags get no local version part (`0.2.dev3`, not `0.2.dev3+gabc1234`), since PyPI and TestPyPI reject local versions.

citefield is distributed on PyPI only. conda, Docker and Homebrew are out of scope.

## Consequences

- A release is a tag push plus an approval. The version can't drift from the tag, and `uv.lock` doesn't change on new commits or tags.
- Every build needs the git tags: CI jobs that build the package check out with `fetch-depth: 0`, and a build from a copy without git metadata fails. The sdist carries its version, so builds from it work.
- A tag that isn't a canonical version, such as `v0.2.0-rc1`, fails the release before anything is published.
- Dev versions no longer say which commit they came from, so `citefield --version` from a source checkout shows the distance from the last tag only.
- The maintainer sets up the trusted publishers on PyPI and TestPyPI and the GitHub environments by hand, once. [docs/guides/releasing.md](../guides/releasing.md) lists the steps.
- Revisit if citefield needs other channels (conda, Docker) or a changelog that is more than PR titles.
