# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Scripts for working with git repositories.
Mostly just convenience stuff because windows scripting sucks.
(Just try to have a daily scheduled task running `git commit -m "Daily commit, {date}"` with the current date.

The scripts also serves as reference/example for how to use various python git packages and the subprocess module.


"""


import sys
import os
import shlex
import subprocess
import click
from datetime import datetime
import git


@click.command()
@click.option(
    '--path', default='.',
    help="The directory to invoke the commands in. Defaults to the current directory.")
@click.option(
    '--branch',
    help="The branch to perform the operations on, defaulting to the currently checked out branch.")
@click.option(
    '--msg-fmt', default="Commit, {date:%Y-%m-%d}.",
    help='The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".')
@click.option(
    '--show-status/--no-show-status', default=False,
    help="Show `git status` after adding files, before commit.")
@click.option(
    '--add-all/--no-add-all', default=False,
    help="Add all files (including untracked files). Only files excluded by .gitignore will not be included.")
@click.option(
    '--dry-run/--no-dry-run', default=False,
    help="Don't add or commit any files, just run the commands as though you would.")
@click.option(
    '--verbose/--no-verbose', default=True,
    help="Enable verbose output when adding and committing files (includes diff of all added files!).")
@click.option(
    '--pause/--no-pause', default=False,
    help="Pause at end of script (by waiting for user input).")
def git_add_and_commit_to_branch_script(path='.', branch=None, msg_fmt="Commit, {date:%Y-%m-%d}.",
                                        show_status=False, add_all=False, dry_run=False, verbose=True, pause=False):
    """ Simple, subprocess-based version of `git_add_and_commit_to_branch` below.
    This is basically an augmented shell script, using the subprocess module to invoke git commands.

    Args:
        path: The directory to invoke the commands in. Defaults to the current directory.
        branch: The branch to perform the operations on, defaulting to the currently checked out branch.
        msg_fmt: The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".
        show_status: Show `git status` after adding files, before commit.
        add_all: Add all files (including untracked files). Only files excluded by .gitignore will not be included.
        dry_run: Don't add or commit any files, just run the commands as though you would.
        verbose: Enable verbose output when adding and committing files (includes diff of all added files!).
        pause: Pause at end of script (by waiting for user input).

    Returns:
        Nothing.
    """
    original_dir = os.getcwd()
    os.chdir(path)
    absdir = os.path.realpath(path)
    print("\n\nRepository:", os.getcwd(), file=sys.stderr)

    commit_msg = msg_fmt.format(date=datetime.now())
    git_add_args = []  # verbose, dry-run.
    git_commit_args = ['-m', commit_msg]

    if verbose:
        git_add_args.append('--verbose')
        # git_commit_args.append('--verbose')  # Verbose commit will show diffs for all committed files!
    if dry_run:
        git_add_args.append('--dry-run')
        git_commit_args.append('--dry-run')

    if branch:
        print(f"\nChecking out branch {branch!r} from repository '{absdir}'.", file=sys.stderr)
        subprocess.run(['git', 'checkout', branch], shell=True, check=True)

    if add_all:
        git_add_args.append('--all')

    print(f"Adding files to the index of branch {branch} in {absdir} ...", file=sys.stderr)
    print("add_args:", git_add_args, file=sys.stderr)
    subprocess.run(['git', 'add'] + git_add_args, shell=True, check=True)

    if show_status:
        # --untracked-files=all can also be written -uall.
        # git status --verbose also does a diff on staged files.
        subprocess.run(['git', 'status', '--untracked-files=all'], shell=True, check=True)

    print(f"\nCommitting {'to branch ' + branch if branch else ''} in {absdir}: \"{commit_msg}\"", file=sys.stderr)
    subprocess.run(['git', 'commit']+git_commit_args, shell=True, check=True)
    os.chdir(original_dir)
    if pause:
        input("\nPress enter to continue...")


@click.command()
@click.option('--branch')
@click.option('--msg-fmt', default="Commit, {date:%Y-%m-%d}.")
@click.option('--git-dir')
@click.option('--work-tree', default=".")
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--add-args', default="")
@click.option('--add-new/--no-add-new', default=True)
@click.option('--add-deleted/--no-add-deleted', default=True)
@click.option('--add-modified/--no-add-modified', default=True)
@click.option('--add-verbose/--no-add-verbose', default=True)
@click.option('--show-status/--no-show-status', default=False)
@click.option('--pause/--no-pause', default=False)
def git_add_and_commit_to_branch(
        branch=None, msg_fmt="Commit, {date:%Y-%m-%d}.",
        # work_tree=".", git_dir=None,
        path=".",
        add_args="",  # "-v -A",
        add_new=True,  # add_untracked=False,  # new are untracked.
        add_modified=True, add_deleted=True, add_verbose=True, show_status=False,
        dry_run=False,
        pause=False,
):
    """ Add and commit

    Args:
        path: The directory to invoke the commands in. Defaults to the current directory.
        branch: The branch to perform the operations on, defaulting to the currently checked out branch.
        msg_fmt: The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".
        msg_fmt: Message (format string)
        path: Path to the git repository or work-tree / working directory.
        add_args: Custom `git add` args. Disables all other `add_*` arguments.
        add_new: Add new (untracked) files.
        add_modified: Add modified files (tracked).
        add_deleted: Add deleted files.
        add_verbose: Use verbose output when adding files. Includes a diff of added files.
        show_status: Show `git status` after adding files, before commit.
        dry_run: Don't add or commit any files, just run the commands as though you would.
        pause:

    Returns:

    """
    absdir = os.path.realpath(path)
    print("path:", absdir)
    repo = git.Repo(path)
    if branch:
        print(f"Checking out branch {branch!r} from repository '{absdir}'.", file=sys.stderr)
        head = repo.branches[branch]
        head.checkout()
        # OBS: You can also use git directly with `repo.git.checkout(branch)`
    else:
        branch = repo.active_branch

    if not add_args:  # User can specify add arguments manually.
        if add_verbose:
            add_args += " -v"
        if add_new:
            add_args += " -A"
        else:
            if add_deleted:
                add_args += " -u"
            elif add_modified:
                add_args += " --no-all ."
            else:
                # Not adding anything; leave add_args empty:
                pass
    if add_args and add_args != "no":
        add_args = shlex.split(add_args)
        print(f"Adding files to the index of branch {branch} in {absdir} ...", file=sys.stderr)
        print("add_args:", add_args, file=sys.stderr)
        if not dry_run:
            print(repo.git.add(add_args))

    if show_status:
        # --untracked-files=all can also be written -uall.
        # git status --verbose also does a diff on staged files.
        print(repo.git.status())

    # Make commit:
    commit_msg = msg_fmt.format(date=datetime.now())
    print(f"Committing to branch {branch} in {absdir}: {commit_msg}", file=sys.stderr)
    if not dry_run:
        print(repo.index.commit(message=commit_msg))
    # repo.git.commit(['-m', commit_msg])  # Commit using git CLI
    if pause:
        input("\nPress enter to continue...")
