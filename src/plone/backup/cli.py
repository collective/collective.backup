"""The plone-backup command."""

from plone.backup import scripts

import argparse
import logging
import os
import pprint
import shlex
import shutil
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="plone-backup",
        description=(
            "Backup and restore a Plone/Zope filestorage and blobstorage "
            "with sensible defaults around repozo. Run one of the backup or "
            "restore commands directly, or generate scripts for them. "
            f"Configure it in the [tool.{scripts.PYPROJECT_TABLE}] table of "
            f"pyproject.toml, or with {scripts.ENV_PREFIX}* variables in a "
            ".env file or in the environment."
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        help=(
            f"read the [tool.{scripts.PYPROJECT_TABLE}] table from this file, "
            f"default: {scripts.PYPROJECT} in the current directory, if it has "
            "this table.  Relative paths are relative to its directory."
        ),
    )
    parser.add_argument(
        "-e",
        "--env-file",
        help=(
            f"read {scripts.ENV_PREFIX}* variables from this file, "
            f"default: {scripts.ENV_FILE} next to the configuration file, or in "
            "the current directory.  These variables win over the configuration "
            "file, and variables in the environment win over both."
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
            "print a crontab using the cron option for backup and the "
            "snapshot_cron option for snapshotbackup"
        ),
    )
    for command, description in scripts.DESCRIPTIONS.items():
        subparser = subparsers.add_parser(command, help=description)
        scripts.add_script_arguments(subparser, command)
    args = parser.parse_args(argv)
    # Show warnings while computing the options, like buildout did.
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    try:
        config = scripts.Config(config=args.config, env_file=args.env_file)
        if args.command == "crontab":
            print(crontab(config, explicit=args), end="")
            return 0
        part = config.part()
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


def crontab(config, explicit=None):
    """Return a crontab for the scheduled backups.

    We first change to the directory of the configuration,
    so the job finds the same configuration and .env file.
    Options that were given explicitly on the command line are passed on.
    """
    program = shutil.which("plone-backup") or os.path.join(
        os.path.dirname(sys.executable), "plone-backup"
    )
    command = f"cd {shlex.quote(config.directory)} && {shlex.quote(program)}"
    if explicit is not None and explicit.config:
        command += f" --config {shlex.quote(config.config_path)}"
    if explicit is not None and explicit.env_file:
        command += f" --env-file {shlex.quote(config.env_file)}"
    lines = []
    for option, name in (("cron", "backup"), ("snapshot_cron", "snapshotbackup")):
        schedule = config.options.get(option, "").strip()
        if schedule:
            lines.append(f"{schedule} {command} {name}\n")
    if not lines:
        raise scripts.ConfigError(
            "Set the cron and/or snapshot_cron option to a cron schedule, "
            f"for example {scripts.ENV_PREFIX}CRON='0 3 * * *'."
        )
    return "".join(lines)
