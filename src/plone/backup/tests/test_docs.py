"""Doctest runner for plone.backup.

The doctests run in a temporary sample project, with a mock repozo script.
They can use helper functions like write, ls and system, and the
'generate' and 'plone_backup' commands.
"""

from plone.backup import cli
from plone.backup import copyblobs
from plone.backup import repozorunner
from plone.backup import scripts
from plone.backup import utils

import doctest
import os
import pytest
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SAMPLE = "/sample-project"
optionflags = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE


class Checker(doctest.OutputChecker):
    """Output checker that normalizes paths and removes DEBUG lines."""

    def __init__(self, replacements):
        self.replacements = replacements

    def normalize(self, text):
        for pattern, replacement in self.replacements:
            text = pattern.sub(replacement, text)
        return text

    def check_output(self, want, got, optionflags):
        return super().check_output(want, self.normalize(got), optionflags)

    def output_difference(self, example, got, optionflags):
        return super().output_difference(example, self.normalize(got), optionflags)


def write(*args):
    *path, contents = args
    with open(os.path.join(*path), "w") as myfile:
        myfile.write(contents)


def cat(*path):
    with open(os.path.join(*path)) as myfile:
        print(myfile.read(), end="")


def mkdir(*path):
    os.mkdir(os.path.join(*path))


def remove(*path):
    path = os.path.join(*path)
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def ls(dir, *subs):
    if subs:
        dir = os.path.join(dir, *subs)
    for name in sorted(os.listdir(dir)):
        path = os.path.join(dir, name)
        if os.path.isdir(path):
            print("d ", name)
        elif os.path.islink(path):
            print("l ", name)
        else:
            print("- ", name)


def system(command, input=""):
    env = dict(os.environ, COLUMNS="80", PYTHONWARNINGS="ignore")
    proc = subprocess.run(
        command,
        shell=True,
        input=input.encode(),
        capture_output=True,
        env=env,
    )
    return (proc.stdout + proc.stderr).decode()


def setUp(test):
    test.orig_dir = os.getcwd()
    test.tmp_dir = os.path.realpath(tempfile.mkdtemp())
    sample = os.path.join(test.tmp_dir, "sample-project")
    os.mkdir(sample)
    os.chdir(sample)
    replacements = [
        (re.compile(r"DEBUG:.*"), ""),  # Remove DEBUG lines.
        (re.compile(re.escape(sample)), SAMPLE),
    ]
    if test.tmp_dir.startswith("/private/"):
        # macOS: /var is a symlink to /private/var
        replacements.append((re.compile(re.escape(sample[8:])), SAMPLE))
    test.checker = Checker(replacements)

    # Add mock ``bin/repozo`` script that prints the options it is passed.
    repozo_output = os.path.join(test.tmp_dir, "repozo-output")
    repozo_script_text = f"#!/bin/sh\necho $* >> {repozo_output}\n"
    os.mkdir("bin")
    write("bin", "repozo", repozo_script_text)
    os.chmod(os.path.join("bin", "repozo"), 0o755)
    mkdir("var")

    def check_repozo_output():
        # Print output and empty the file.
        if os.path.exists(repozo_output):
            with open(repozo_output) as myfile:
                print(myfile.read())
            os.remove(repozo_output)
        else:
            print()

    # Incremental blob backups need GNU tar.  On macOS it is available as gtar.
    test.orig_path = os.environ["PATH"]
    gtar = shutil.which("gtar")
    if gtar:
        gnubin = os.path.join(test.tmp_dir, "gnubin")
        os.mkdir(gnubin)
        os.symlink(gtar, os.path.join(gnubin, "tar"))
        os.environ["PATH"] = gnubin + os.pathsep + test.orig_path

    test.globs.update(
        {
            "REPOZO_SCRIPT_TEXT": repozo_script_text,
            "cat": cat,
            "check_repozo_output": check_repozo_output,
            "generate": f"{sys.executable} -m plone.backup generate",
            "plone_backup": f"{sys.executable} -m plone.backup",
            "join": os.path.join,
            "ls": ls,
            "mkdir": mkdir,
            "remove": remove,
            "sample_project": sample,
            "system": system,
            "write": write,
        }
    )


def tearDown(test):
    os.environ["PATH"] = test.orig_path
    os.chdir(test.orig_dir)
    shutil.rmtree(test.tmp_dir)


DOCFILES = sorted(
    name for name in os.listdir(os.path.dirname(__file__)) if name.endswith(".rst")
)
MODULES = [utils, repozorunner, scripts, copyblobs, cli]


def run_suite(suite):
    # The checker is created per test in setUp, so we patch it in here.
    result = unittest.TestResult()
    for case in suite:
        orig_setup = case._dt_setUp

        def set_up(test, orig_setup=orig_setup, case=case):
            orig_setup(test)
            case._dt_checker = test.checker

        case._dt_setUp = set_up
        case.run(result)
    messages = [text for _case, text in result.failures + result.errors]
    assert not messages, "\n".join(messages)


@pytest.mark.parametrize("docfile", DOCFILES)
def test_docfile(docfile):
    run_suite(
        doctest.DocFileSuite(
            docfile, setUp=setUp, tearDown=tearDown, optionflags=optionflags
        )
    )


@pytest.mark.parametrize("module", MODULES, ids=lambda module: module.__name__)
def test_module_doctests(module):
    run_suite(
        doctest.DocTestSuite(
            module, setUp=setUp, tearDown=tearDown, optionflags=optionflags
        )
    )
