.. NOTE: You should *NOT* be adding new change log entries to this file, this
         file is managed by towncrier. You *may* edit previous change logs to
         fix problems like typo corrections or such.

         To add a new change log entry, please see the notes from the ``pip`` project at
             https://pip.pypa.io/en/latest/development/#adding-a-news-entry

.. towncrier release notes start

1.0.0a1 (unreleased)
--------------------

- Initial release.  Backup and restore a ZODB filestorage and blobstorage
  with ``repozo``, with sensible defaults.  Commands: ``backup``,
  ``snapshotbackup``, ``zipbackup``, ``restore``, ``snapshotrestore``,
  ``ziprestore`` and ``altrestore``.
  [jladage]

- Run the commands with ``collective-backup <command>``, or generate scripts like
  ``bin/backup`` and ``bin/restore`` with ``collective-backup generate``.
  ``collective-backup show`` shows the computed options.
  [jladage]

- Configure it in the ``[tool.collective-backup]`` table of ``pyproject.toml``,
  with ``COLLECTIVE_BACKUP_*`` variables in a ``.env`` file, or with environment
  variables.
  [jladage]

- Schedule backups with the ``cron`` and ``snapshot_cron`` options:
  ``collective-backup crontab`` prints a crontab for them.
  [jladage]

- Add a ``Dockerfile`` for an image that runs the scheduled backups,
  for use next to the ``plone/plone-backend`` and ``plone/plone-zeo`` images.
  [jladage]
