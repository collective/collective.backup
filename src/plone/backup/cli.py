"""The plone-backup command."""

from plone.backup import scripts

import argparse
import logging
import os
import pprint
import shutil
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="plone-backup",
        description=(
            "Backup and restore a Plone/Zope filestorage and blobstorage "
            "with sensible defaults around repozo. Run one of the backup or "
            "restore commands directly, or generate scripts for them. "
            f"Configure it with {scripts.ENV_PREFIX}* environment variables."
        ),
    )
    parser.add_argument(
        "-e",
        "--env-file",
        help=(
            f"read {scripts.ENV_PREFIX}* variables from this file, "
            f"default: {scripts.ENV_FILE} in the current directory, if it exists. "
            "Variables in the environment win."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser(
        "generate", help="generate the backup and restore scripts"
    )
    generate.add_argument(
        "--bin-dir",
        help=f"directory for the scripts, default: {scripts.ENV_PREFIX}BIN_DIR or 'bin'",
    )
    subparsers.add_parser("show", help="show the computed options")
    subparsers.add_parser(
        "crontab",
        help=(
            f"print a crontab using {scripts.ENV_PREFIX}CRON for backup and "
            f"{scripts.ENV_PREFIX}SNAPSHOT_CRON for snapshotbackup"
        ),
    )
    for command, description in scripts.DESCRIPTIONS.items():
        subparser = subparsers.add_parser(command, help=description)
        scripts.add_script_arguments(subparser, command)
    args = parser.parse_args(argv)
    # Show warnings while computing the options, like buildout did.
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    try:
        if args.command == "crontab":
            print(crontab(args.env_file), end="")
            return 0
        part = scripts.load_part(args.env_file)
        if args.command == "generate":
            scripts.generate(part, bin_dir=args.bin_dir)
            return 0
        if args.command == "show":
            print(f"name = {part.name!r}")
            print(f"scripts = {sorted(part.commands().values())!r}")
            print(pprint.pformat(part.arguments))
            return 0
        if args.command not in part.commands():
            raise scripts.ConfigError(f"The {args.command} command is not enabled.")
    except scripts.ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return scripts.execute(args.command, part.arguments, args)


def crontab(env_file=None):
    """Return a crontab for the scheduled backups.

    >>> print(crontab(), end='')
    Traceback (most recent call last):
    ...
    plone.backup.scripts.ConfigError: Set PLONE_BACKUP_CRON and/or PLONE_BACKUP_SNAPSHOT_CRON...
    >>> os.environ['PLONE_BACKUP_CRON'] = '0 3 * * *'
    >>> print(crontab(), end='')
    0 3 * * * .../plone-backup backup
    >>> os.environ['PLONE_BACKUP_SNAPSHOT_CRON'] = '@weekly'
    >>> print(crontab(), end='')
    0 3 * * * .../plone-backup backup
    @weekly .../plone-backup snapshotbackup
    >>> del os.environ['PLONE_BACKUP_CRON']
    >>> del os.environ['PLONE_BACKUP_SNAPSHOT_CRON']
    """
    variables = {}
    if env_file:
        variables.update(scripts.read_env_file(env_file))
    elif os.path.isfile(scripts.ENV_FILE):
        variables.update(scripts.read_env_file(scripts.ENV_FILE))
    variables.update(os.environ)
    program = shutil.which("plone-backup") or os.path.join(
        os.path.dirname(sys.executable), "plone-backup"
    )
    if env_file:
        program += f" --env-file {os.path.abspath(env_file)}"
    lines = []
    for variable, command in (("CRON", "backup"), ("SNAPSHOT_CRON", "snapshotbackup")):
        schedule = variables.get(scripts.ENV_PREFIX + variable, "").strip()
        if schedule:
            lines.append(f"{schedule} {program} {command}\n")
    if not lines:
        raise scripts.ConfigError(
            f"Set {scripts.ENV_PREFIX}CRON and/or {scripts.ENV_PREFIX}SNAPSHOT_CRON "
            "to a cron schedule, for example '0 3 * * *'."
        )
    return "".join(lines)
