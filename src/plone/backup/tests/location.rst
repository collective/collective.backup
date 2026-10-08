# -*-doctest-*-

Location
========

You should not mix backup locations; it is confusing for the recipe
(or at least its authors) when backups end up in the same directory::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_LOCATION=loc1
    ... PLONE_BACKUP_BLOBBACKUPLOCATION=loc1
    ... PLONE_BACKUP_SNAPSHOTLOCATION=loc2
    ... PLONE_BACKUP_BLOBSNAPSHOTLOCATION=loc2
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
    ... PLONE_BACKUP_BLOB_STORAGE=var/blobstorage
    ... PLONE_BACKUP_ENABLE_ZIPBACKUP=true
    ... PLONE_BACKUP_LOCATION=
    ... PLONE_BACKUP_BLOBBACKUPLOCATION=
    ... PLONE_BACKUP_SNAPSHOTLOCATION=
    ... PLONE_BACKUP_BLOBSNAPSHOTLOCATION=
    ... PLONE_BACKUP_ZIPLOCATION=
    ... PLONE_BACKUP_BLOBZIPLOCATION=
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

The recipe tests the ``location`` option, to see if it will be able to
create folders when scripts are called.

We'll use all options, except the blob options for now::

    >>> write('.env',
    ... """
    ... PLONE_BACKUP_BACKUP_BLOBS=false
    ... PLONE_BACKUP_LOCATION=/my/unusable/path/for/backup
    ... """)
    >>> print(system(generate))
    Generated script '/sample-project/bin/backup'.
    Generated script '/sample-project/bin/snapshotbackup'.
    Generated script '/sample-project/bin/restore'.
    Generated script '/sample-project/bin/snapshotrestore'.
    Removed script '/sample-project/bin/zipbackup'.
    Removed script '/sample-project/bin/ziprestore'.
    utils: WARNING: Not able to create /my/unusable/path/for/backup
