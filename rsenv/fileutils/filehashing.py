import hashlib


from .fileutils import kB, MB, GB

CHUNK_SIZE = 64*kB


def calculate_file_hash(
        filepath, hashmethod='md5',
        read_start=0, read_limit=0, chunk_size=CHUNK_SIZE, return_type='hex'):
    """ Calculate file hash.

    This function will read file given by `filepath` and feed the bytes read to the given hashing method.
    It is possible to specify a byte limit, e.g. only read the first 100000 bytes.
    Bytes are read until EOF or the number of bytes read exceeds the limit, if given.

    Hashing method can be e.g. 'md5', 'sha256' or any other method from the hashlib standard library package.
    The hasing method can also be a custom hashing method (object instance), which must implement
    the same interface as the hashing methods from the `hashlib` package. (`update()`, `digest()`, `hexdigest()`).

    Args:
        filepath: Path of the file to read and calculate hash from.
        hashmethod: The hash method to use to calculate file hash, e.g. 'md5' or 'sha256'.
        read_start: Seek the file to this byte offset before starting to read and calculate hash.
        read_limit: The maximum number of bytes to read from file, useful for large files.
        chunk_size: The number of bytes to read from file and feed to the hashing method in every loop.
        return_type: The digest type to return, e.g. 'hex' (string), int (integer), or 'bytes' (default).

    Returns:
        Hash digest, as specificed by return_type.

    """
    if isinstance(hashmethod, str):
        hashfactory = getattr(hashlib, hashmethod)
        hashmethod = hashfactory()
    with open(filepath, "rb") as f:
        if read_start and read_start > 0:
            f.seek(read_start)
        n_bytes_read = 0
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hashmethod.update(chunk)
            n_bytes_read += chunk_size
            if 0 < read_limit < n_bytes_read:
                break
    if return_type == 'hex':
        return hashmethod.hexdigest()
    elif return_type == 'int':
        # Note: Python ints limited to 64bits = 8 bytes, else error: "int too big to convert".
        return int.from_bytes(hashmethod.digest()[:8], byteorder='little')
    else:
        return hashmethod.digest()



