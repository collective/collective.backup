# -*-doctest-*-

Location
========

You should not mix backup locations; it is confusing for us when backups end up in the same directory::

    >>> write('.env',
    ... """
    ... COLLECTIVE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... COLLECTIVE_BACKUP_LOCATION=loc1
    ... COLLECTIVE_BACKUP_BLOBBACKUPLOCATION=loc1
    ... COLLECTIVE_BACKUP_SNAPSHOTLOCATION=loc2
    ... COLLECTIVE_BACKUP_BLOBSNAPSHOTLOCATION=loc2
    ... """)
    >>> print(system(generate))
    Error: These must be distinct locations:
    blobbackuplocation = loc1
    blobsnapshotlocation = loc2
    location = loc1
    snapshotlocation = loc2

Some of these locations might be an empty string in some cases, which
is probably grudgingly allowed, at least by this particular check.

    >>> write('.env',
    ... """
    ... COLLECTIVE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... COLLECTIVE_BACKUP_ENABLE_ZIPBACKUP=true
    ... COLLECTIVE_BACKUP_LOCATION=
    ... COLLECTIVE_BACKUP_BLOBBACKUPLOCATION=
    ... COLLECTIVE_BACKUP_SNAPSHOTLOCATION=
    ... COLLECTIVE_BACKUP_BLOBSNAPSHOTLOCATION=
    ... COLLECTIVE_BACKUP_ZIPLOCATION=
    ... COLLECTIVE_BACKUP_BLOBZIPLOCATION=
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/zipbackup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/ziprestore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    <BLANKLINE>


Unexisting backup location
--------------------------

We test the ``location`` option, to see if it will be able to
create folders when scripts are called.

We'll use all options, except the blob options for now::

    >>> write('.env',
    ... """
    ... COLLECTIVE_BACKUP_BACKUP_BLOBS=false
    ... COLLECTIVE_BACKUP_LOCATION=/my/unusable/path/for/backup
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Removed script '/sample-project/bin/zipbackup'.
    Removed script '/sample-project/bin/ziprestore'.
    utils: WARNING: Not able to create /my/unusable/path/for/backup
