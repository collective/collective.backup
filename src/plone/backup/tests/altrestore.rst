# -*-doctest-*-

Alternative restore sources
===========================

Create directories::

    >>> mkdir('alt')
    >>> mkdir('alt', 'data')
    >>> mkdir('alt', 'blobs')

You can restore from an alternative source.  Use case: first make a
backup of your production site, then go to the testing or staging
server and restore the production data there.  This is supported with
the ``alternative_restore_source`` option::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Generated script '/sample-project/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Created directory /sample-project/var/filestorage
    INFO: Please wait while restoring database file: /sample-project/alt/data to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/alt/data

Add original blobstorage (usually this is the blobstorage of a Zope
instance or ZEO server, but we do it simpler here) but forget to
add it to the alternative::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data
    ... """)
    >>> print(system(generate))
    Error: alternative_restore_source key 'Data' is missing a blobdir.
    <BLANKLINE>

Add blobstorage to the alternative, but not the original::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data alt/blobs
    ... """)
    >>> print(system(generate))
    Error: alternative_restore_source key 'Data' specifies blobdir 'alt/blobs' but the original storage has no blobstorage.

Add blobstorage to original and alternative::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data alt/blobs
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Generated script '/sample-project/bin/altrestore'.
    <BLANKLINE>

Call the script::

    >>> ls('var')
    d  filestorage
    >>> remove('var', 'filestorage')
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)? INFO: Created directory /sample-project/var/filestorage
    ERROR: There are no backups in /sample-project/alt/blobs.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>
    >>> ls('var')
    d  filestorage

Create the necessary sample directories and call the script again::

    >>> mkdir('alt', 'blobs', 'blobstorage.0')
    >>> mkdir('alt', 'blobs', 'blobstorage.0', 'blobstorage')
    >>> write('alt', 'blobs', 'blobstorage.0', 'blobstorage', 'blobfile.txt', 'Hello blob.')
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/alt/data to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/alt/blobs to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/alt/blobs/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/alt/data
    >>> ls('var')
    d  blobstorage
    d  filestorage
    >>> ls('var', 'blobstorage')
    -   blobfile.txt
    >>> cat('var', 'blobstorage', 'blobfile.txt')
    Hello blob.

Calling the script with a specific date is supported just like the
normal restore script.  If the date is too early, the real repozo script would fail,
saying 'No files in repository before <date>'.  Our mock repozo script would accept it,
but we have added a check in the blob restore so we now fail as well.

    >>> print(system('bin/altrestore 2000-12-31-23-59', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 2000-12-31-23-59.
    ERROR: Could not find backup of '2000-12-31-23-59' or earlier.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>

So test is with a date in the future::

    >>> print(system('bin/altrestore 2100-12-31-23-59', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 2100-12-31-23-59.
    INFO: Please wait while restoring database file: /sample-project/alt/data to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/alt/blobs to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/alt/blobs/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/alt/data -D 2100-12-31-23-59

When archive_blob is true, we use it::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_ARCHIVE_BLOB=true
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data alt/blobs
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Generated script '/sample-project/bin/altrestore'.
    <BLANKLINE>
    >>> print(system('bin/backup'))
    INFO: Created /sample-project/var/backups
    INFO: Created /sample-project/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragebackups
    INFO: tar cf /sample-project/var/blobstoragebackups/blobstorage.20....tar  -C /sample-project/var/blobstorage .
    INFO: Creating symlink from latest to blobstorage.20....tar
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip
    >>> remove('alt', 'data')
    >>> remove('alt', 'blobs')
    >>> print(system('mv var/backups alt/data'))
    >>> print(system('mv var/blobstoragebackups alt/blobs'))
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-project/alt/data to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/alt/blobs to /sample-project/var/blobstorage
    INFO: Removing /sample-project/var/blobstorage
    INFO: Extracting /sample-project/alt/blobs/blobstorage.20....tar to /sample-project/var/blobstorage
    INFO: tar xf /sample-project/alt/blobs/blobstorage.20....tar  -C /sample-project/var/blobstorage
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/alt/data
    >>> ls('var', 'blobstorage')
    -   blobfile.txt

When the name is not ``backup``, we end up with different names for
the scripts.  You can use several env files to generate several sets
of scripts::

    >>> write('first.env',
    ... """
    ... PLONE_BACKUP_NAME=firstbackup
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data
    ... """)
    >>> write('second.env',
    ... """
    ... PLONE_BACKUP_NAME=secondbackup
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data alt/data
    ... """)
    >>> print(system(plone_backup + ' -e second.env generate'))
    Generated script '/sample-project/bin/secondbackup'.
    Generated script '/sample-project/bin/secondbackup-snapshot'.
    Generated script '/sample-project/bin/secondbackup-restore'.
    Generated script '/sample-project/bin/secondbackup-snapshotrestore'.
    Generated script '/sample-project/bin/secondbackup-altrestore'.
    <BLANKLINE>
    >>> print(system(plone_backup + ' -e first.env generate'))
    Generated script '/sample-project/bin/firstbackup'.
    Generated script '/sample-project/bin/firstbackup-snapshot'.
    Generated script '/sample-project/bin/firstbackup-restore'.
    Generated script '/sample-project/bin/firstbackup-snapshotrestore'.
    Generated script '/sample-project/bin/firstbackup-altrestore'.
    <BLANKLINE>


Corner cases
------------

Specifying ``1`` instead of ``Data`` is fine::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=1 alt/data
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Generated script '/sample-project/bin/altrestore'.
    <BLANKLINE>
    >>> print(system('bin/altrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/alt/data to /sample-project/var/filestorage/Data.fs
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/alt/data

Specifying both ``1`` and ``Data`` is bad.
Only one line is supported anyway::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE="1 alt/one\\nData alt/data"
    ... """)
    >>> print(system(generate))
    Error: Only one alternative_restore_source line is supported.

Unknown keys are bad::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=foo alt/foo
    ... """)
    >>> print(system(generate))
    Error: alternative_restore_source key 'foo' unknown. Expected 1 or Data.

A filestorage source path is required::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ALTERNATIVE_RESTORE_SOURCE=Data
    ... """)
    >>> print(system(generate))
    Error: alternative_restore_source line 'Data' has a wrong format. Should be: 'storage-name filestorage-backup-path', optionally followed by a blobstorage-backup-path.
