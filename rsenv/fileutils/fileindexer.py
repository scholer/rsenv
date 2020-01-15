

"""

This module is for creating and updating a basic index of local files.

The purpose is to have a single text file that I can keep under revision control,
which tracks changes to all my files.

The index is just a dataframe, each row being a file on disk,
with column containing various file information - including
path, filesize, modification time, checksum hashes, etc.

Creating the index is very simple, just find all files from the root and get corresponding file info.

Updating the index efficiently is a bit more tricky.

* We don't want to calculate full file checksum hashes for every update.
* We need to determine what files have been modified since last run.
* Only hash new or modified files.
* If a file has been renamed, we also don't want to do a complete re-hash.
* It should be safe to use filesize, modtime (or just full fstat).



Design:

* Service + clients design.
* The indexing service runs e.g. nightly (when computer is not used).
* The indexing service updates the index, calculating hash for new files.
* A CLI search client, that searches the index for files matching a given query.
    * The search client includes a feature/option to search for files with
      hash identical to a given file: `--same-hash-as-file <path-to-file>`.
    * Consider also creating a "folder index", where the hash is just the hash of the files and
      subfolders added together. You can have two different hashes, one that includes
      filenames and one that is just based on file content.




Prior art:
-----------

Git:
* Git keeps an index.
* Git tracks: path, ctime, mtime, dev, ino, uid, gid, size, flags.
* Use `git ls-files --debug` to see info.
* Refs:
    * https://mirrors.edge.kernel.org/pub/software/scm/git/docs/technical/racy-git.txt
    * https://mirrors.edge.kernel.org/pub/software/scm/git/docs/git-update-index.html


Pandas:
* Refs:
    * http://pandas.pydata.org/pandas-docs/version/0.22/generated/pandas.DataFrame.groupby.html


Woosh ID GNU/Linux tools
* "Whoosh is a library of classes and functions for indexing text and then searching the index."
* (I don't want to index text, but I do want to be able to tell if files needs to be re-indexed or not.)
    This is called "Incremental indexing" in Woosh.
* Woosh tools
    * https://github.com/fiatjaf/washer
    * https://github.com/knipknap/whooshstore
    * http://whoosh.readthedocs.io/en/latest/indexing.html

OS File indexing services:

* Windows Search and Indexing service.
* Tracker (GNOME's File Indexing And Search Tool)

File systems:

* Recollfs
    * https://github.com/pidlug/recollfs


Search tools:

* DocFetcher - Java
* Cerebro - Javascript.
* Zeitgeist - Vala, Python, C++.
    * logs the users’s activities and events.
* Synapse - Uses Zeitgeist indexing engine. By Michal Hruby.
* axosynaptic - based on Synapse.
* Everything - By Void Tools. Freeware, not open-source.
    * But has SDK, https://www.voidtools.com/support/everything/sdk/
    * Python example: https://www.voidtools.com/forum/viewtopic.php?f=10&t=8245&sid=39512c428dfa9413808a0c5e1a3c031d

* FSearch -
* ULauncher
* ANGRYsearch
* Catfish


Thought: Would it be possible to hook into existing search applications, adding the ability
to search by file-hash?

* Other launchers have implemented file-search using everything:
    * https://github.com/oliverschwendener/ueli/issues/93




File and directory comparison toolsÆ

* Fingerprint, https://github.com/ioquatix/fingerprint
* dtreetrawl, https://github.com/raamsri/dtreetrawl


"""



