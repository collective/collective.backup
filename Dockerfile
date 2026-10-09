# syntax=docker/dockerfile:1
# Image that makes scheduled backups of a Plone filestorage and blobstorage.
# Configure it with COLLECTIVE_BACKUP_* environment variables, see README.rst.
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
COPY . /src
RUN python -m venv /app \
    && /app/bin/pip install --no-cache-dir /src

FROM python:${PYTHON_VERSION}-slim
ARG TARGETARCH
ARG SUPERCRONIC_VERSION=v0.2.49
ARG SUPERCRONIC_SHA1SUM_amd64=e63c11a9726b775a6a11801e81af4f3fb926aa68
ARG SUPERCRONIC_SHA1SUM_arm64=0b6c5bb743e0b0dafed1132198c81807927ac413

LABEL org.opencontainers.image.title="collective-backup" \
      org.opencontainers.image.description="Scheduled backups of a Plone filestorage and blobstorage with repozo" \
      org.opencontainers.image.source="https://github.com/collective/collective.backup" \
      org.opencontainers.image.licenses="GPL-2.0-only"

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl rsync; \
    case "${TARGETARCH:-amd64}" in \
        amd64) sha1="${SUPERCRONIC_SHA1SUM_amd64}" ;; \
        arm64) sha1="${SUPERCRONIC_SHA1SUM_arm64}" ;; \
        *) echo "Unsupported architecture ${TARGETARCH}"; exit 1 ;; \
    esac; \
    curl -fsSLo /usr/local/bin/supercronic \
        "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${TARGETARCH:-amd64}"; \
    echo "${sha1}  /usr/local/bin/supercronic" | sha1sum -c -; \
    chmod +x /usr/local/bin/supercronic; \
    apt-get purge -y curl; \
    apt-get autoremove -y; \
    rm -rf /var/lib/apt/lists/*; \
    # Same uid and gid as the plone user in the plone/plone-backend image,
    # so we can read and restore its files.
    groupadd --system --gid 500 plone; \
    useradd --system --uid 500 --gid plone --home-dir /app --no-create-home plone; \
    mkdir -p /data /backups; \
    chown plone:plone /data /backups

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
