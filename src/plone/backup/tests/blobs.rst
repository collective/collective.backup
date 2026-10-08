# -*-doctest-*-

Blob storage
============

For tests with ``blob_timestamps = true``, see ``blob_timestamps.rst``.
That started as a copy of the current ``blobs.rst`` file.
At first, ``blob_timestamps = false`` was the default.
Since version 4.2 the default is True.
We might make timestamps the only supported way in the future.

By default we backup the blobs in ``var/blobstorage``.
You can turn this off::

    >>> mkdir('var', 'filestorage')
    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65

Full cycle tests:

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_KEEP=3
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65
    >>> ls('bin')
    -  backup
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> mkdir('var/blobstorage')
    >>> write('var', 'blobstorage', 'blob1.txt', 'Sample blob 1.')

Test the snapshotbackup first, as that should be easiest.

    >>> print(system('bin/snapshotbackup'))
    INFO: Created /sample-project/var/snapshotbackups
    INFO: Created /sample-project/var/blobstoragesnapshots
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragesnapshots
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups -F --gzip
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    >>> ls('var/blobstoragesnapshots/blobstorage.0')
    d  blobstorage

Let's try that some more, with a second in between so we can more
easily test restoring to a specific time later.

    >>> import time
    >>> time.sleep(2)
    >>> write('var', 'blobstorage', 'blob2.txt', 'Sample blob 2.')
    >>> print(system('bin/snapshotbackup'))
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragesnapshots
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-project/var/blobstorage /sample-project/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups -F --gzip
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    >>> cat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob1.txt')
    Sample blob 1.
    >>> cat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob2.txt')
    Sample blob 2.
    >>> cat('var/blobstoragesnapshots/blobstorage.1/blobstorage/blob1.txt')
    Sample blob 1.

Now remove an item:

    >>> time.sleep(2)
    >>> remove('var', 'blobstorage', 'blob2.txt')
    >>> print(system('bin/snapshotbackup'))
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/var/snapshotbackups
    INFO: Please wait while making snapshot of blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragesnapshots
    INFO: Renaming blobstorage.1 to blobstorage.2.
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-project/var/blobstorage /sample-project/var/blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups -F --gzip
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    d  blobstorage.2
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.2/blobstorage')
    -  blob1.txt

Let's see how a bin/backup goes:

    >>> print(system('bin/backup'))
    INFO: Created /sample-project/var/backups
    INFO: Created /sample-project/var/blobstoragebackups
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragebackups
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    >>> ls('var/blobstoragebackups/blobstorage.0')
    d  blobstorage
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt

We try again with an extra 'blob':

    >>> time.sleep(2)
    >>> write('var', 'blobstorage', 'blob2.txt', 'Sample blob 2.')
    >>> print(system('bin/backup'))
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragebackups
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a  --delete --link-dest=../blobstorage.1 /sample-project/var/blobstorage /sample-project/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    d  blobstorage.1
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragebackups/blobstorage.1/blobstorage')
    -  blob1.txt

Let's check the inodes of two files, to see if they are the same.  Not
sure if this works on all operating systems.

    >>> import os
    >>> stat_0 = os.stat('var/blobstoragebackups/blobstorage.0/blobstorage/blob1.txt')
    >>> stat_1 = os.stat('var/blobstoragebackups/blobstorage.1/blobstorage/blob1.txt')
    >>> stat_0.st_ino == stat_1.st_ino
    True

We could to things differently for the snapshot blob backups, as they
should be full copies, but using hard links they also really are full
copies, so also in this case the inodes can be the same::

    >>> stat_0 = os.stat('var/blobstoragesnapshots/blobstorage.0/blobstorage/blob1.txt')
    >>> stat_1 = os.stat('var/blobstoragesnapshots/blobstorage.1/blobstorage/blob1.txt')
    >>> stat_0.st_ino == stat_1.st_ino
    True

Now try a restore::

    >>> print(system('bin/restore', input='no\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Not restoring.
    <BLANKLINE>
    >>> print(system('bin/restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragebackups to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobstoragebackups/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

With the ``no-prompt`` option we avoid the question::

    >>> print(system('bin/restore --no-prompt'))
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragebackups to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobstoragebackups/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

Since release 2.3 we can also restore blobs to a specific date/time.
blobstorage.0 is the newest, blobstorage.1 is the oldest.  The restore
script will restore the first blobstorage with a modification time the
same or earlier than the time we ask for.  Here we ask for a time that
should be the same as the modification date of blobstorage.1.  We
add a second to avoid random errors that have plagued these
tests due to rounding or similar sillyness.

    >>> mod_time_0 = os.path.getmtime('var/blobstoragebackups/blobstorage.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragebackups/blobstorage.1')
    >>> mod_time_0 > mod_time_1
    True
    >>> from datetime import datetime
    >>> time_string = '-'.join(['{0:02d}'.format(t) for t in datetime.utcfromtimestamp(mod_time_1 + 1).timetuple()[:6]])
    >>> print(system('bin/restore %s' % time_string, input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragebackups to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobstoragebackups/blobstorage.1/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups -D ...

The second blob file is now no longer in the blob storage.

    >>> ls('var/blobstorage')
    -  blob1.txt

When passed a date for which we have no backups, the script will fail.

    >>> print(system('bin/restore 1972-12-25', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at 1972-12-25.
    ERROR: Could not find backup of '1972-12-25' or earlier.
    ERROR: Halting execution: restoring blobstorages would fail.
    <BLANKLINE>
    >>> check_repozo_output()

The snapshotrestore works too::

    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/snapshotbackups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragesnapshots to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobstoragesnapshots/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups

Check that this fits what is in the most recent snapshot::

    >>> ls('var/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots')
    d  blobstorage.0
    d  blobstorage.1
    d  blobstorage.2
    >>> ls('var/blobstoragesnapshots/blobstorage.0/blobstorage')
    -  blob1.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.1/blobstorage')
    -  blob1.txt
    -  blob2.txt
    >>> ls('var/blobstoragesnapshots/blobstorage.2/blobstorage')
    -  blob1.txt

Since release 2.3 we can also restore blob snapshots to a specific date/time.

    >>> mod_time_0 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.0')
    >>> mod_time_1 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.1')
    >>> mod_time_2 = os.path.getmtime('var/blobstoragesnapshots/blobstorage.2')
    >>> mod_time_0 > mod_time_1
    True
    >>> mod_time_1 > mod_time_2
    True
    >>> time_string = '-'.join(['{0:02d}'.format(t) for t in datetime.utcfromtimestamp(mod_time_1 + 1).timetuple()[:6]])
    >>> print(system('bin/snapshotrestore %s' % time_string, input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Date restriction: restoring state at ...
    INFO: Please wait while restoring database file: /sample-project/var/snapshotbackups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/blobstoragesnapshots to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobstoragesnapshots/blobstorage.1/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/snapshotbackups -D ...

The second blob file was only in blobstorage snapshot number 1 when we
started and now it is also in the main blobstorage again.

    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

When repozo quits with an error, we should not restore the blobs then either.
We test that with a special bin/repozo script that simply quits::

    >>> import sys
    >>> write('bin', 'repozo', '#!%s\nimport sys\nsys.exit(1)' % sys.executable)
    >>> dontcare = system('chmod u+x bin/repozo')
    >>> print(system('bin/snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/snapshotbackups to /sample-project/var/filestorage/Data.fs
    ERROR: Repozo command failed. See message above.
    ERROR: Halting execution due to error; not restoring blobs.
    <BLANKLINE>
    >>> check_repozo_output()

Restore the original bin/repozo::

    >>> write('bin', 'repozo', REPOZO_SCRIPT_TEXT)
    >>> dontcare = system('chmod u+x bin/repozo')

We can tell buildout that we only want to backup blobs or specifically
do not want to backup the blobs.

When we explicitly set backup_blobs to true, without blob_storage option,
we use ``var/blobstorage``::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BACKUP_BLOBS=true
    ... """)
    >>> print(system(plone_backup + ' show'))
    name = 'backup'
    ...
                 'blobdir': '/sample-project/var/blobstorage',
    ...

Combining blob_backup=false and only_blobs=true will not work::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_ONLY_BLOBS=true
    ... """)
    >>> print(system(generate))
    Error: Cannot have backup_blobs false and only_blobs true.
    <BLANKLINE>

Specifying backup_blobs and only_blobs might be useful in case you
want to separate this into several scripts.  Let's specify
enable_zipbackup too::

    >>> write('file.env',
    ... """
    ... PLONE_BACKUP_NAME=filebackup
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... """)
    >>> write('blob.env',
    ... """
    ... PLONE_BACKUP_NAME=blobbackup
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_ONLY_BLOBS=true
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=true
    ... """)
    >>> print(system(plone_backup + ' -e file.env generate'))
    Generated script '/sample-project/bin/filebackup'.
    Generated script '/sample-project/bin/filebackup-snapshot'.
    Generated script '/sample-project/bin/filebackup-restore'.
    Generated script '/sample-project/bin/filebackup-snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65
    >>> print(system(plone_backup + ' -e blob.env generate'))
    Generated script '/sample-project/bin/blobbackup'.
    Generated script '/sample-project/bin/blobbackup-zip'.
    Generated script '/sample-project/bin/blobbackup-snapshot'.
    Generated script '/sample-project/bin/blobbackup-restore'.
    Generated script '/sample-project/bin/blobbackup-ziprestore'.
    Generated script '/sample-project/bin/blobbackup-snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65

Now we test it.  First the backup.  The filebackup now only backs up
the filestorage::

    >>> print(system('bin/filebackup'))
    INFO: Created /sample-project/var/filebackups
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/filebackups
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/filebackups --quick --gzip

blobbackup only backs up the blobstorage::

    >>> print(system('bin/blobbackup'))
    INFO: Created /sample-project/var/blobbackup-blobstorages
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobbackup-blobstorages
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/var/blobbackup-blobstorages/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()

Test the snapshots as well::

    >>> print(system('bin/filebackup-snapshot'))
    INFO: Created /sample-project/var/filebackup-snapshots
    INFO: Please wait while making snapshot backup: /sample-project/var/filestorage/Data.fs to /sample-project/var/filebackup-snapshots
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/filebackup-snapshots -F --gzip
    >>> print(system('bin/blobbackup-snapshot'))
    INFO: Created /sample-project/var/blobbackup-blobstoragesnapshots
    INFO: Please wait while making snapshot of blobs from /sample-project/var/blobstorage to /sample-project/var/blobbackup-blobstoragesnapshots
    INFO: rsync -a  /sample-project/var/blobstorage /sample-project/var/blobbackup-blobstoragesnapshots/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()

Now test the restore::

    >>> print(system('bin/filebackup-restore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/filebackups to /sample-project/var/filestorage/Data.fs
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/filebackups
    >>> print(system('bin/filebackup-snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the filestorage:
        /sample-project/var/filestorage/Data.fs
    Are you sure? (yes/No)?
    INFO: Please wait while restoring database file: /sample-project/var/filebackup-snapshots to /sample-project/var/filestorage/Data.fs
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/filebackup-snapshots
    >>> print(system('bin/blobbackup-restore', input='yes\n'))
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-project/var/blobbackup-blobstorages to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobbackup-blobstorages/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> print(system('bin/blobbackup-snapshotrestore', input='yes\n'))
    <BLANKLINE>
    This will replace the blobstorage:
        /sample-project/var/blobstorage
    Are you sure? (yes/No)?
    INFO: Restoring blobs from /sample-project/var/blobbackup-blobstoragesnapshots to /sample-project/var/blobstorage
    INFO: rsync -a  --delete /sample-project/var/blobbackup-blobstoragesnapshots/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()

Test extra rsync options, currently only testing --no-l -k to allow
for symlinked directory dereferencing in restore. We use this to test
passing of valid rsync options additional to the default -a
option. Since all backup and restore variants with blobs and using
rsync use the same code, we only need to test the standard backup and
restore to ensure passing of extra options to rsync works::

    >>> # first remove some previously created directories interfering with this test
    >>> import shutil
    >>> shutil.rmtree('var/blobstoragebackups/blobstorage.0')
    >>> shutil.rmtree('var/blobstoragebackups/blobstorage.1')
    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_RSYNC_OPTIONS=--no-l -k
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65
    >>> ls('bin')
    -  backup
    -  blobbackup
    -  blobbackup-restore
    -  blobbackup-snapshot
    -  blobbackup-snapshotrestore
    -  blobbackup-zip
    -  blobbackup-ziprestore
    -  filebackup
    -  filebackup-restore
    -  filebackup-snapshot
    -  filebackup-snapshotrestore
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> print(system('bin/backup'))
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragebackups
    INFO: rsync -a --no-l -k /sample-project/var/blobstorage /sample-project/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip
    >>> ls('var/blobstoragebackups')
    d  blobstorage.0
    >>> ls('var/blobstoragebackups/blobstorage.0')
    d  blobstorage
    >>> ls('var/blobstoragebackups/blobstorage.0/blobstorage')
    -  blob1.txt
    -  blob2.txt

So backup still works, now test restore that uses a symlinked directory as the backup source::

    >>> # first remove blobs from blobstorage as we are testing restore
    >>> remove('var','blobstorage','blob1.txt')
    >>> remove('var','blobstorage','blob2.txt')
    >>> mkdir('var/test')
    >>> mkdir('var/test/blobstorage.0')
    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_BLOBBACKUPLOCATION=test
    ... PLONE_BACKUP_RSYNC_OPTIONS=--no-l -k
    ... # we use pre_ and post_commands to set/unset the symlink
    ... # using os.symlink instead causes rsync to fail for some reason
    ... PLONE_BACKUP_PRE_COMMAND=ln -s $PWD/var/blobstoragebackups/blobstorage.0/blobstorage $PWD/var/test/blobstorage.0/blobstorage
    ... PLONE_BACKUP_POST_COMMAND=unlink $PWD/var/test/blobstorage.0/blobstorage
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65
    >>> ls('bin')
    -  backup
    -  blobbackup
    -  blobbackup-restore
    -  blobbackup-snapshot
    -  blobbackup-snapshotrestore
    -  blobbackup-zip
    -  blobbackup-ziprestore
    -  filebackup
    -  filebackup-restore
    -  filebackup-snapshot
    -  filebackup-snapshotrestore
    -  repozo
    -  restore
    -  snapshotbackup
    -  snapshotrestore
    >>> print(system('bin/restore --no-prompt'))
    <BLANKLINE>
    INFO: Please wait while restoring database file: /sample-project/var/backups to /sample-project/var/filestorage/Data.fs
    INFO: Restoring blobs from /sample-project/var/test to /sample-project/var/blobstorage
    INFO: rsync -a --no-l -k --delete /sample-project/var/test/blobstorage.0/blobstorage /sample-project/var
    <BLANKLINE>
    >>> check_repozo_output()
    --recover -o /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups
    >>> ls('var/blobstorage')
    -  blob1.txt
    -  blob2.txt

A blob_storage with a slash at the end can give unexpected results, creating a backup with name ``.0``.
See issue #26. So test what happens:

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_TIMESTAMPS=false
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage/
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    backup: You have disabled blob_timestamps. Support for this may be dropped in a future version, making it impossible to restore backups without timestamps. See https://github.com/collective/collective.recipe.backup/issues/65
    >>> print(system('bin/backup'))
    INFO: Please wait while backing up database file: /sample-project/var/filestorage/Data.fs to /sample-project/var/backups
    INFO: Please wait while backing up blobs from /sample-project/var/blobstorage to /sample-project/var/blobstoragebackups
    INFO: Renaming blobstorage.0 to blobstorage.1.
    INFO: rsync -a --delete --link-dest=../blobstorage.1 /sample-project/var/blobstorage /sample-project/var/blobstoragebackups/blobstorage.0
    <BLANKLINE>
    >>> check_repozo_output()
    --backup -f /sample-project/var/filestorage/Data.fs -r /sample-project/var/backups --quick --gzip
