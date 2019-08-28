# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Scripts for working with git repositories.
Mostly just convenience stuff because windows scripting sucks.
(Just try to have a daily scheduled task running `git commit -m "Daily commit, {date}"` with the current date.

The scripts also serves as reference/example for how to use various python git packages and the subprocess module.


Libraries for working with Git and git repositories:


Low-level libraries:

* gitdb
    * https://github.com/gitpython-developers/gitdb
* dulwich
    * https://github.com/dulwich/dulwich
* pygit2
    * https://github.com/libgit2/pygit2
    * "Python bindings for libgit2"
    * https://www.pygit2.org/

High-level libraries:

* gitpython
    * https://github.com/gitpython-developers/GitPython
    * Uses gitdb.
    * WARNING: Does not appear to support worktrees,
        i.e. working inside a `reposotory.git` repo, which
        uses `core.worktree` config to specify the worktree path.
    * More references on the worktree issue:
        * https://github.com/datalad/datalad/issues/753
    * Actually, I think the core.worktree support has been added with this commit from Sep 28, 2018:
        https://github.com/gitpython-developers/GitPython/commit/530ab00f28262f6be657b8ce7d4673131b2ff34a
    * I'm currently using gitpython 2.1.11, released Jul 15, 2018. This is currently the most recent release,
        so if I want to support core.worktree config option, I have to pip-install the latest git master from github.
        pip install git+git@github.com:gitpython-developers/GitPython.git or maybe
        pip install git+https://github.com/gitpython-developers/GitPython.git
    * Workarounds:
        1. Use a newer version of gitpython.
        2. Monkey-patch the repo object?
        3. Use dulwich?
        4. For the script CLI, you only need gitpython for checking if the repository has staged changes.
            You can also check this using a git shell command, e.g.:
                `git diff --quiet --exit-code --cached`
                gives nonzero exit code if there are outstanding changes staged.
            subprocess.run() returns a CompletedProcess object with a `returncode` attribute.
            In Windows CMD, check exit code with `echo %errorlevel%`.
            By the way, `git diff --cached` is more reliable than `git diff-index`, since `git diff-index` may report
            changes if the files have been touched but not actually changed.
    * Does dulwich support worktrees?
        * PR implementing worktree support: https://github.com/dulwich/dulwich/pull/454
    * WARNING: "As GitPython is in maintenance mode, I won't be adding any new features."
        from: https://github.com/gitpython-developers/GitPython/issues/344
    * So, I guess that means gitpython is becoming obsolte?
* gittle
    * https://github.com/FriendCode/gittle
    * Uses dulwich.
    * "Pythonic Git for Humans"
    * Last commit was 3 years ago??
        * https://github.com/keyser-fr/gittle - the most recent fork, still 2 years old.
    * OBS: pip-installing gittle failed miserably for me in my rsenv conda environment.

Git CLIs (prior art):

* legit
    * https://github.com/kennethreitz/legit
    * Git for Humans, Inspired by GitHub for Mac™.
    * Uses gitpython.

* datalad
    * https://github.com/datalad/datalad
    * "Keep scientific data under control with git and git-annex http://datalad.org".
    *




## Comparisons:

Gittle:

```
repo = Gittle.clone(repo_url, repo_path)  # or Gittle.init(path)
repo.commits  # Get list of objects
repo.branches  # List of branches
repo.modified_files  # List of modified files.
```


How to see if there are uncommitted changes:

* https://stackoverflow.com/questions/5139290/how-to-check-if-theres-nothing-to-be-committed-in-the-current-branch
```
git status --porcelain
git diff --exit-code
git diff --cached --exit-code
git ls-files --other --exclude-standard --directory
```


Adding colors:

In your git config:
```
[color]
  diff = auto
  status = auto
  branch = auto
  interactive = auto
  ui = true
  pager = true

[color "status"]
  added = green
  changed = red bold
  untracked = magenta bold

[color "branch"]
  remote = yellow

```

Colors can be enabled and disabled on a per-invocation basis using `git -c configkey=value`:

    git -c color.status=false status

However, it is required that the `-c key=value` option is before the `status` command.



"""


import sys
import os
import subprocess
import shlex
import click
from datetime import datetime
import git


def repo_has_uncommitted_staged_changes(path):
    completed_proc = subprocess.run(shlex.split('git --no-pager diff --quiet --exit-code --cached'))
    # A non-zero exit code means it has staged, uncommitted changes:
    return completed_proc.returncode != 0


@click.command()
@click.option(
    '--path', '-p', default=None, multiple=True,
    help="The directory to invoke the commands in. Defaults to the current directory.")
@click.option(
    '--branch', '-b',
    help="The branch to perform the operations on, defaulting to the currently checked out branch.")
@click.option(
    '--msg-fmt', '-m', default="Commit, {date:%Y-%m-%d}.",
    help='The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".')
@click.option(
    '--add-all/--no-add-all', '-A', default=False,
    help="Add all files (including untracked files). Only files excluded by .gitignore will not be included.")
@click.option(
    '--show-compact-summary/--no-show-compact-summary', default=False,
    help="Show `git diff --compact-summary` before adding files, before commit. Implies --stat.")
@click.option(
    '--show-status/--no-show-status', default=False,
    help="Show `git status` after adding files, before commit.")
@click.option(
    '--dry-run/--no-dry-run', '-n', default=False,
    help="Don't add or commit any files, just run the commands as though you would.")
@click.option(
    '--verbose/--no-verbose', '-v', default=True,
    help="Enable verbose output when adding and committing files (includes diff of all added files!).")
@click.option(
    '--pause/--no-pause', '-w', default=False,
    help="Pause at end of script (by waiting for user input).")
@click.option(
    '--pause-on-error/--no-pause-on-error', default=False,
    help="Pause if errors are encountered during script (asking user to abort or continue).")
def git_add_and_commit_script(
        path='.', branch=None, msg_fmt="Commit, {date:%Y-%m-%d}.",
        add_all=False, show_compact_summary=False, show_status=False, dry_run=False, verbose=True, pause=False, pause_on_error=False
):
    """ Add and commit changed files to branch in git repository.
    This is a simple, subprocess-based version of `git_add_and_commit_to_branch` below.
    This is basically an augmented shell script, using the subprocess module to invoke git commands.
    Note that `git.cwd` is also just using the subprocess module to invoke git commands,
    so this is really not much different.

    While this function is more basic, it has the advantage of natively producing colored output,
    without hacking around too much with `gitpython`.

    Args:
        path: The directory (or directories) to invoke the commands in. Defaults to the current directory.
        branch: The branch to perform the operations on, defaulting to the currently checked out branch.
        msg_fmt: The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".
        add_all: Add all files (including untracked files). Only files excluded by .gitignore will not be included.
        show_compact_summary: Show `git diff --compact-summary` before adding files, before commit.
        show_status: Show `git status` after adding files, before commit.
        dry_run: Don't add or commit any files, just run the commands as though you would.
        verbose: Enable verbose output when adding files (includes diff of all added files!).
        pause: Pause at end of script (by waiting for user input).

    Returns:
        Nothing.

    TODO: Consider using the `sh` module to create the shell commands.
    """
    if not path:
        path = ['.']
    if isinstance(path, str):
        path = [path]
    run_date = datetime.now()
    print(f"\n\n\n[{run_date:%Y-%m-%d %H:%m}] git-add-and-commit-script paths: {path}")
    original_dir = os.getcwd()

    for repo_path in path:
        repo = git.Repo(repo_path)
        cfg = repo.config_reader()
        core_worktree = cfg.get('core', 'worktree')
        if core_worktree:
            pass
        os.chdir(repo_path)
        absdir = os.path.realpath(repo_path)
        run_date = datetime.now()
        print("\n\n     - - - - - - - - - - - - - - - - - -      ")
        print(
            f"\n\n[{run_date:%Y-%m-%d %H:%m}] git-add-and-commit-script started for repository: {absdir}",
            file=sys.stderr
        )
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
            git_checkout_cmd = ['git', 'checkout', branch]
            if branch not in repo.heads:
                print(f"\nWARNING: branch '{branch}' not present in repository '{absdir}'")
                ans = input(
                    f"Would you like to [skip] this repository, [abort] run, or [create] this branch? [S/a/c] "
                ).lower() or 's'
                if ans[0] == 'a':
                    print(" - OK, ABORTING RUN.")
                    exit(1)
                elif ans[0] == 'c':
                    print(f" - OK, will create branch '{branch}'.")
                    git_checkout_cmd = ['git', 'checkout', '-b', branch]
                elif ans[0] == 's':
                    print(" - OK, Skipping repository {absdir}.")
                    continue
                else:
                    print("Answer not recognized; skipping.")
                    continue
            print(f"\nChecking out branch {branch!r} from repository '{absdir}'.", file=sys.stderr)
            try:
                # Checking out the already-active branch will just give output "Already on 'daily_commits'".
                subprocess.run(git_checkout_cmd, shell=True, check=True)
            except subprocess.CalledProcessError as exc:
                print(f"Error checking out branch '{branch}': {exc}")
                print(" - ")
                if pause_on_error:
                    ans = input("Press Enter to continue. Press 'a'+enter or Ctrl+c to abort...")
                    if ans and ans.lower()[0] == 'a':
                        exit(exc.returncode or 1)
                else:
                    raise exc
        else:
            branch = str(repo.active_branch)

        if show_compact_summary:
            # Use `git diff` to see difference between worktree and index;
            # Use `git diff --cached` to see difference between index and HEAD;
            # Use `git diff HEAD` to see difference between worktree and HEAD;
            print(f"\nCompact-summary diff between working directory and HEAD of branch '{branch}'", file=sys.stderr)
            subprocess.run(['git', '--no-pager', 'diff', '--compact-summary', 'HEAD'], shell=True, check=True)

        if add_all:
            git_add_args.append('--all')
        else:
            git_add_args.append('--update')

        print(
            f"\nAdding files to the index of branch '{branch}' in '{absdir}' using args `{' '.join(git_add_args)}`.",
            file=sys.stderr
        )
        subprocess.run(['git', '--no-pager', 'add'] + git_add_args, shell=True, check=True)

        if show_status:
            # --untracked-files=all can also be written -uall.
            # git status --verbose also does a diff on staged files.
            print("\nStatus:", file=sys.stderr)
            subprocess.run(['git', '--no-pager', 'status', '--untracked-files=all'], shell=True, check=True)

        # OBS: We should check if there actually is anything to commit,
        # otherwise, `git-commit will yield an error.
        # repo.index.diff()  # will diff the index against itself, yielding an empty diff.
        # repo.index.diff(None)  # will diff the index against the working tree.
        # repo.index.diff('HEAD')  # will diff the index against the current HEAD.
        # We have just added all changes to the index, so we are diffing the stage against the HEAD.
        # OBS: repo.index.diff('HEAD') will fail if this is a completely new branch with no prior commits.
        # if repo.index.diff('HEAD'):
        if repo_has_uncommitted_staged_changes(absdir):
            print(f"\nCommitting to branch '{branch}' in {absdir}: \"{commit_msg}\".", file=sys.stderr)
            subprocess.run(['git', '--no-pager', 'commit']+git_commit_args, shell=True, check=True)
        else:
            print("\nNo changes staged for commit on the index; skipping commit.", file=sys.stderr)

    os.chdir(original_dir)
    if pause:
        input("\n\nPress enter to continue...")


@click.command()
@click.option('--path', default=".")
@click.option('--branch')
@click.option('--msg-fmt', default="Commit, {date:%Y-%m-%d}.")
@click.option('--add-all/--no-add-all', default=False)
@click.option('--show-status/--no-show-status', default=False)
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--verbose/--no-verbose', default=True)
@click.option('--pause/--no-pause', default=False)
def git_add_and_commit_to_branch(
        path=".", branch=None, msg_fmt="Commit, {date:%Y-%m-%d}.",
        add_all=False, show_status=False, dry_run=False, verbose=True, pause=False,
):
    """ Add and commit changed files to branch in git repository.
    OBS: This CLI version is mostly here to demonstrate how to use gitpython,
    in comparison with using the git CLI directly.

    Args:
        path: Path to the git repository or work-tree / working directory. Defaults to the current directory.
        branch: The branch to perform the operations on, defaulting to the currently checked out branch.
        msg_fmt: The commit message - can include formatting variables. Default: "Commit, {date:%Y-%m-%d}.".
        add_all: Add all files including new/untracked files. (But not ignored files, obviously.)
        show_status: Show `git status` after adding files, before commit.
        dry_run: Don't add or commit any files, just run the commands as though you would.
        verbose: Enable verbose output when adding files (includes diff of all added files!).
        pause: Pause at end of script (by waiting for user input).

    Disabled args (these just made everything more complicated - just stick to standard git behavior):
        add_args: Custom `git add` args. Disables all other `add_*` arguments.
        add_new: Add new (untracked) files.
        add_modified: Add modified files (tracked).
        add_deleted: Add deleted files.


    Returns:
        Nothing.

    OBS: What `git.Repo.git.<command>` does (as defined in `git.cmd`) is really not much different
    from just calling `git <command>` shell command via `subprocess`. (`git.cmd` uses `subprocess.Popen`)
    """
    absdir = os.path.realpath(path)
    run_date = datetime.now()
    print(
        f"\n\n[{run_date:%Y-%m-%d %H:%m}] git-add-and-commit-to-branch started for repository: {absdir}",
        file=sys.stderr
    )
    commit_msg = msg_fmt.format(date=datetime.now())
    git_add_args = []  # verbose, dry-run.
    git_commit_args = ['-m', commit_msg]
    if verbose:
        git_add_args.append('--verbose')
        # git_commit_args.append('--verbose')  # Verbose commit will show diffs for all committed files!
    if dry_run:
        git_add_args.append('--dry-run')
        git_commit_args.append('--dry-run')

    repo = git.Repo(path)
    if branch:
        print(f"\nChecking out branch {branch!r} from repository '{absdir}'.", file=sys.stderr)
        head = repo.heads[branch]  # repo.heads is same property as repo.branches
        head.checkout()  # Alternatively, use git directly with `repo.git.checkout(branch)`
    else:
        branch = repo.active_branch

    if add_all:
        git_add_args.append('--all')
    else:
        git_add_args.append('--update')

    print(
        f"\nAdding files to the index of branch '{branch}' in '{absdir}' using args `{' '.join(git_add_args)}` ...",
        file=sys.stderr
    )
    print(repo.git.add(git_add_args))

    if show_status:
        # git status --verbose also does a diff on staged files (can produce very long output).
        print("\nStatus:")
        print(repo.git.status('-u'))  # -u is alias for -uall which is alias for --untracked-files=all

    # Make commit:
    # OBS: Unlike the git CLI, gitpython's repo.index.commit() works just fine even for an empty commit.
    # However, we generally don't want to litter the log with empty commits, so check anyways.
    if repo.index.diff('HEAD'):
        print(f'\nCommitting to branch {branch} in {absdir}: "{commit_msg}"', file=sys.stderr)
        if not dry_run:
            print(repo.index.commit(message=commit_msg))
            # repo.git.commit(['-m', commit_msg])  # Alternatively, commit using git CLI
    else:
        print("\nNo changes staged for commit on the index; skipping commit.")

    if pause:
        input("\nPress enter to continue...")
