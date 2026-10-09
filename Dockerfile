# syntax=docker/dockerfile:1
# Image that makes scheduled backups of a Plone filestorage and blobstorage.
# Configure it with COLLECTIVE_BACKUP_* environment variables, see README.rst.
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
ARG TARGETARCH
ARG SUPERCRONIC_VERSION=v0.2.49
ARG SUPERCRONIC_SHA1SUM_amd64=e63c11a9726b775a6a11801e81af4f3fb926aa68
ARG SUPERCRONIC_SHA1SUM_arm64=0b6c5bb743e0b0dafed1132198c81807927ac413

COPY . /src
# Install with the pip of the builder, so the venv has no pip or setuptools.
# Drop the tests and C sources that the ZODB packages ship.
RUN set -eux; \
    python -m venv --without-pip /app; \
    pip --python /app/bin/python install --no-cache-dir /src; \
    find /app/lib -depth \
        \( -type d -name tests -o -name '*.c' -o -name '*.h' \) \
        -exec rm -rf {} +

# Download supercronic here, so the image needs no curl or ca-certificates.
ADD https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${TARGETARCH} /supercronic
RUN set -eux; \
    case "${TARGETARCH}" in \
        amd64) sha1="${SUPERCRONIC_SHA1SUM_amd64}" ;; \
        arm64) sha1="${SUPERCRONIC_SHA1SUM_arm64}" ;; \
        *) echo "Unsupported architecture ${TARGETARCH}"; exit 1 ;; \
    esac; \
    echo "${sha1}  /supercronic" | sha1sum -c -; \
    chmod +x /supercronic

FROM python:${PYTHON_VERSION}-slim

LABEL org.opencontainers.image.title="collective-backup" \
      org.opencontainers.image.description="Scheduled backups of a Plone filestorage and blobstorage with repozo" \
      org.opencontainers.image.source="https://github.com/collective/collective.backup" \
      org.opencontainers.image.licenses="GPL-2.0-only"

# The plone user has the same uid and gid as in the plone/plone-backend
# image, so we can read and restore its files.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends rsync; \
    rm -rf /var/lib/apt/lists/*; \
    groupadd --system --gid 500 plone; \
    useradd --system --uid 500 --gid plone --home-dir /app --no-create-home plone; \
    mkdir -p /data /backups; \
    chown plone:plone /data /backups

COPY --from=builder /supercronic /usr/local/bin/supercronic
COPY --from=builder /app /app
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# The plone/plone-backend image keeps its data in /data.
# Backups go to /backups, which you should mount as a separate volume.
ENV PATH="/app/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    COLLECTIVE_BACKUP_VAR_DIR=/data \
    COLLECTIVE_BACKUP_LOCATIONPREFIX=/backups \
    COLLECTIVE_BACKUP_CRON="0 3 * * *"

USER plone
WORKDIR /app
VOLUME ["/backups"]
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["cron"]
