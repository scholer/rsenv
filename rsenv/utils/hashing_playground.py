# Copyright 2019, Rasmus Sorensen <rasmusscholer@gmail.com>
"""

Module for playing around with different hashing functions.

For instance, how to create a general-purpose hashing function that takes an object
hashes it without using json or similar text-serialization.

You could consider using pickle instead of json?

"""


HASHABLE_TYPES = {
    list,
    set,
    tuple,
    str,
    int,
    float,
    bytes,
}


def lists_and_dicts_to_tuples_recursively(obj):
    """ Convert all lists to tuples and all dicts to tuples of (k, v) pairs.
    OBS: This is a one-way conversion and indistinguishable from a nested-tuples
    data-structure to begin with.
    """
    if isinstance(obj, list):
        return tuple(lists_and_dicts_to_tuples_recursively(v) for v in obj)
    elif isinstance(obj, dict):
        return tuple((k, lists_and_dicts_to_tuples_recursively(v)) for k, v in obj.items())
    else:
        return obj


def recursive_hashing(m, obj):
    """

    Args:
        m:
        obj:

    Returns:

    Discussion: How to distinguish types?
    * I guess I could just add that as a tuple, so:
        1 --> ('int', 1)
    * While if the input was `('int', 1)`, the output would be
        ('int', 1)  -->  (('str', 'int'), ('int', 1)).

    What are good ways to hash python objects/values?
    * The built-in hash() function is designed to change from run to run (except for simple values),
      so that is a no-go.
    * Use the hashlib functions, feeding bytes to a hash machine.

    Other discussions:
    * https://bugs.python.org/issue15814 - discussion of hashing memory-views.

    """

    hash_bits = m.digest_size * 8
    hash_modulus = 2**hash_bits

    if isinstance(obj, str):
        # Strings are byte-encoded using UTF-8:
        m.update(obj.encode('utf8'))
    elif isinstance(obj, (int, float)):
        # Should 1 (int) hash to the same as '1' (str) ?
        # Or should we use int.to_bytes(n_bytes, byteorder) to convert to bytes?
        # You can use n_bytes = (int.bit_length() // 8) + 1 to get the number of bytes required.
        # But what about float?
        m.update(str(obj).encode('utf8'))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            recursive_hashing(m, v)
    elif isinstance(obj, set):
        # Order-independent hashing:
        # Or alternatively, just sort before hashing - is effectively order-independent.
        # But what if we cannot sort the elements? Nah, we can always do that.
        set_hash_int = 0
        for elem in obj:
            elem_hash_dig = recursive_hashing(hashlib.new(m.name), elem)
            elem_hash_int = int.from_bytes(elem_hash_dig, byteorder='big')
            set_hash_int = (set_hash_int + elem_hash_int) % hash_modulus
        set_hash_dig = int.to_bytes(set_hash_int, m.digest_size, byteorder='big')
        m.update(set_hash_dig)
    elif isinstance(obj, dict):
        # A dict is a set of (key, value) tuples:
        recursive_hashing(set(obj.items()))
    else:
        raise TypeError(f"Unrecognized type {type(obj)} for object {obj!r}.")

    return m.digest()
    # return int.from_bytes(m.digest(), byteorder='big')
