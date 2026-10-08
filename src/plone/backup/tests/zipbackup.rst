# -*-doctest-*-

zipbackup and ziprestore
========================

Since version 2.20, we can create a zipbackup and ziprestore
script.  These use a different backup location and have a few options
hardcoded: archive_blob is True, keep is 1, regardless of what
the options in the buildout recipe section are.  You can always create
a separate buildout section where you explicitly change this using
options for the standard bin/backup script.

By default the scripts are not created.  You can ensable the them by
setting the enable_zipbackup option to true.

Create directories and content::

    >>> mkdir('var', 'blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1.')

Create some archived and not-archived separate backup scripts::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... # keep is ignored by the zipbackup script
    ... PLONE_BACKUP_KEEP=42
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=true
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/zipbackup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/ziprestore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    <BLANKLINE>

Now we test it::

    >>> print(system('bin/zipbackup'))
    INFO: Created /sample-project/var/zipbackups
    INFO: Created /sample-project/var/blobstoragezips
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/zipbackups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragezips
    INFO: tar cf /sample-project/var/blobstoragezips/blobstorage.0.tar  -C /sample-project/var/blobstorage .
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/zipbackups -F --gzip

Keep is ignored by zipbackup, always using 1 as value::

    >>> print(system('bin/zipbackup'))
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/zipbackups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragezips
    INFO: Renaming blobstorage.0.tar to blobstorage.1.tar.
    INFO: tar cf /sample-project/var/blobstoragezips/blobstorage.0.tar  -C /sample-project/var/blobstorage .
    INFO: Removed 1 full blob backup, with 1 file. The latest 1 backup has been kept.
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/zipbackups -F --gzip

Now test the ziprestore script::

    >>> print(system('bin/ziprestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Created directory /sample-project/var/filestorage
    INFO: Please wait while restoring database file: /sample-project/var/zipbackups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragezips to /sample-project/var/blobstorage
    INFO: Removing /sample-project/var/blobstorage
    INFO: Extracting /sample-project/var/blobstoragezips/blobstorage.0.tar to /sample-project/var/blobstorage
    INFO: tar xf /sample-project/var/blobstoragezips/blobstorage.0.tar  -C /sample-project/var/blobstorage
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/zipbackups

You can choose not to enable the zip scripts::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_KEEP=42
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=false
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Removed script '/sample-project/bin/zipbackup'.
    Removed script '/sample-project/bin/ziprestore'.
    >>> ls('bin')
    -  backup
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

Or you simply do not list the enable_zipbackup option, falling back to
the default::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_KEEP=42
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    >>> ls('bin')
    -  backup
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore

If backup_blobs is false, it is useless to enable the zipbackup, so we
refuse this combination::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=true
    ... """)
    >>> print(system(generate))
    Error: Cannot have backup_blobs false and enable_zipbackup true. zipbackup is useless without blobs.
