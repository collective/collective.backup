#!/bin/sh
set -e

case "$1" in
    cron)
        # Run the scheduled backups.  supercronic passes the environment,
        # so the COLLECTIVE_BACKUP_* variables reach the backup commands.
        collective-backup crontab > /tmp/crontab
        echo "Scheduled backups:"
        cat /tmp/crontab
        collective-backup show
        exec supercronic /tmp/crontab
        ;;
    backup|zipbackup|snapshotbackup|restore|ziprestore|snapshotrestore|altrestore|show|crontab|generate)
        exec collective-backup "$@"
        ;;
esac
exec "$@"
