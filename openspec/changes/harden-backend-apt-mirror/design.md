## Overview

The backend Docker image should not depend exclusively on `deb.debian.org` or `files.pythonhosted.org` for large package installs. The image build will rewrite Debian apt sources during the build using a configurable `APT_MIRROR` build argument, install apt packages with retry/timeout options, and install Python packages through a configurable PyPI index with longer timeout/retry settings.

## Decisions

- Add `ARG APT_MIRROR=https://mirrors.aliyun.com/debian` near the top of `backend/Dockerfile`.
- Add `ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple` near the top of `backend/Dockerfile`.
- Replace Debian source URLs in `/etc/apt/sources.list.d/debian.sources` with `${APT_MIRROR}` before `apt-get update`.
- Use apt options on `apt-get update` and `apt-get install`:
  - `Acquire::Retries=5`
  - `Acquire::http::Timeout=30`
  - `Acquire::https::Timeout=30`
- Keep the package set unchanged so LaTeX functionality remains the same.
- Run `pip install` with `--index-url`, `--retries`, and `--timeout` values so large packages such as `torch` have a better chance of completing on unstable links.

## Alternatives Considered

- Only add retries: still leaves the build dependent on the failing CDN path.
- Hard-code mirrors with no build args: simpler, but makes non-China or CI environments harder to override.
- Use a full TeX base image: much larger blast radius and unnecessary for this build failure.

## Risks

- A mirror can lag behind Debian or PyPI upstream metadata. The build args allow switching back to official sources or another mirror if needed.
- Corporate networks may block a particular mirror. The build command can override `APT_MIRROR` and `PIP_INDEX_URL`.
