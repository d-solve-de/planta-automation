# planta-filler container image: Python + Firefox ESR + geckodriver.
# Works with Docker and Podman:  docker build -t planta-filler:local .
# See docs/docker.md for how to log in once and run headless afterwards.

FROM python:3.12-slim-bookworm

ARG GECKODRIVER_VERSION=0.36.0

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Firefox ESR (Debian package) and the tools needed to fetch geckodriver.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        ca-certificates curl firefox-esr fonts-dejavu-core; \
    rm -rf /var/lib/apt/lists/*

# geckodriver from the official GitHub release for the image architecture.
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
        amd64) gd_arch="linux64" ;; \
        arm64) gd_arch="linux-aarch64" ;; \
        *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${gd_arch}.tar.gz" \
        | tar -xz -C /usr/local/bin; \
    chmod +x /usr/local/bin/geckodriver; \
    geckodriver --version

# Install the package itself.
WORKDIR /build
COPY pyproject.toml MANIFEST.in README.md LICENSE CHANGELOG.md ./
COPY src ./src
RUN pip install . && rm -rf /build

# Run as an unprivileged user; the Firefox profile lives in a volume.
RUN useradd --create-home --uid 1000 planta \
    && mkdir -p /home/planta/.selenium_profiles /data/reference \
    && chown -R planta:planta /home/planta /data
USER planta
ENV HOME=/home/planta
WORKDIR /home/planta
VOLUME ["/home/planta/.selenium_profiles"]

ENTRYPOINT ["planta-filler"]
CMD ["--help"]
