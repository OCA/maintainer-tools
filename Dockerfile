# An image to run maintainer tools.
# gh auth login (https, browser)
# gh auth setup-git

FROM debian:12-slim

RUN apt-get update  \
    && apt-get -y --no-install-recommends install  \
        sudo curl git ca-certificates build-essential \
        libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev curl \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
        libffi-dev liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

ENV MISE_DATA_DIR="/mise"
ENV MISE_CONFIG_DIR="/mise"
ENV MISE_CACHE_DIR="/mise/cache"
ENV MISE_INSTALL_PATH="/usr/local/bin/mise"
ENV PATH="/mise/shims:$PATH"

RUN curl https://mise.run | sh

COPY mise.toml ${MISE_DATA_DIR}/config.toml
RUN mise install
  
RUN uv venv /venv

# Install maintainer-tools and its dependencies.
COPY . /app
RUN uv pip install --python /venv/bin/python -e /app \
 && ln -s /venv/bin/oca-copier-update /usr/local/bin/

COPY copier-update-all.sh /usr/local/bin
