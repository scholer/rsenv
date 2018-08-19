

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
* If a file has been renamed, we also don't want to do a complete re-hash.
* It should be safe to use filesize, modtime (or just full fstat).






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


Recollfs
* https://github.com/pidlug/recollfs



"""



