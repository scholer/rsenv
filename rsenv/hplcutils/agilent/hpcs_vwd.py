# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

"""

Read HPLC chromatograms from HP/Agilent ChemStation variable-wavelength detector (VWD) data files.

The VWD signal/channel files are typically named something like `vwd1A.ch`.

The libHPCS C library was used as reference to reverse engineer the binary VWD .ch format,
and this code is released under the same license (GPLv3).


Example usage (from a directory containing a vwd1A.ch data file):

    >>> from rsenv.hplcutils.agilent import hpcs_vwd
    >>> data = hpcs_vwd.read_agilent_1200_vwd_ch('vwd1A.ch')
    >>> # `data` is a dict with three items: signal_values, timepoints, and metadata. To plot the data:
    >>> from matplotlib import pyplot; pyplot.ion()
    >>> pyplot.plot(data['timepoints'], data['signal_values'])


Reading binary HPLC data:
  1. Seek to predefined position,
  2. Read the first byte to determine length (N bytes, 1-255).
  3. Read N bytes, unpack with

Other notes:
* struct module uses '>B' is big-endian, but int.from_bytes uses 'big' to specify byteorder.

Observations from an actual vwd1A.ch file:
* Four magic bytes.
* All bytes are in sets of two (i.e. 16 bits), e.g.
    `0331 3330 0000 0000 0000 0000 0000 0000`.
    * Although could perhaps also be sets of 4 bytes = 32 bits.
* Next non-null byte at 16*15+7 = 247 = 0xf7, value is 0x5c = 92.

* The sample information begins at address 0x35a.
* First byte (at 0x35a) is the string length, e.g. 9 for "RS535a-Q2".
* The strings appear to be unicode (two bytes per character). So you must read 2x9 = 18 bytes to get the string.

Parsing file:  vwd1A.ch
Generated by: Agilent 1200 Variable Wavelength Detector.
Acq_Software: ChemStation Rev. B.04.01 [481] by Agilent Technologies


How to read data:

* If the .ch data is similar to what is described in TheTrueTom HP1100SeriesConverter,
    then the data format is a bit complicated.
    First, in order to reduce the data/file size, the program prefers to specify
    *changes* compared to the previous measurement, rather than absolute values.
    However, if the signal changes too much, then we need to "break out" and use absolute values instead.
    Second, instead of using normal floating point values, the program uses integers multiplied by a
    pre-defined constant.

    1. Read 1 byte to determine how many values to read (rec_length).
    2. Read 2 bytes (inp). If these two bytes are 0x8000, then

* Data begins at byte 16*384 = 0x1800.

* \x80\x00 seems to be a special code, perhaps indicating overflow?

* The file ends with a null byte, but also contains plenty of null bytes.


The vwd.ch file uses "Pascal strings":
    "Pascal strings, meaning a short variable-length string stored in a fixed number of bytes, given by the count.
    - from https://docs.python.org/3/library/struct.html


Example: Read sample name:

    # Read sample name:
    f.seek(0x35a)
    strlen = int.from_bytes(f.read(1), 'big')
    samplename_bytes_be = f.read(strlen * 2)
    # We need to convert big-endian bytes to little-endian before we can decode the unicode byte string:
    # Several ways to do this, see e.g.
    # https://stackoverflow.com/questions/846038/convert-a-python-int-into-a-big-endian-string-of-bytes
    # If you need to do it a lot, you can use the scott-griffiths' bitstring package.
    # You can also use e.g. numpy, or just the standard struct module.
    # Note: You need to convert character-by-character. But maybe the easiest is to just take every other character.
    # samplename_bytes_int = int.from_bytes(samplename_bytes_be, 'big')
    # samplename_bytes_le = samplename_bytes_int.to_bytes((samplename_bytes_int.bit_length() + 7) // 8, 'little')
    samplename = samplename_bytes_be[::2].decode('utf-8')



https://github.com/scholer/libHPCS/blob/master/src/libHPCS_p.h
* Has "new" and "old" file versions.
* New version has:

    DATA_SCANS_START = 0x108;           # Mine is \x00 here, but probably because I'm not doing any wavelength scans.
    DATA_OFFSET_XMIN = 0x11A;           # Mine is \x00\x00\x00\x25 here.
    DATA_OFFSEt_XMAX = 0x11E;           # Mine is \x00\x19\xa2\x73 here.
    DATA_OFFSET_FILE_DESC = 0x15B;      # Same as mine ("LC DATA FILE").
    DATA_OFFSET_SAMPLE_INFO = 0x35A;    # Same as mine.
    DATA_OFFSET_OPERATOR_NAME = 0x758;  # Same as mine.
    DATA_OFFSET_DATE = 0x957;           # Same as mine.
    DATA_OFFSET_METHOD_NAME = 0xA0E;    # Same as mine.
    DATA_OFFSET_CS_VER = 0xE11;         # Same as mine.
    DATA_OFFSET_CS_REV = 0xEDA;         # Same as mine.

    DATA_OFFSET_SIGSTEP_VERSION = 0x1026; # Mine is 0x00 here.
    # I don't think this matters, that VERSION is not defined,
    # is just pre-defined step (either 0.1 or 0.0024), and shift (always zero). Else just read from file.
    DATA_OFFSET_SIGSTEP_SHIFT = 0x1274; # Mine is 0x00 here.
    DATA_OFFSET_SIGSTEP_STEP = 0x127C;  # Same as mine? Is \x3f\0f\40\00 = 63 15 64 00
    DATA_OFFSET_Y_UNITS = 0x104C;       # Same as mine.
    DATA_OFFSET_DEVSIG_INFO = 0x1075;   # Same as mine.
    DATA_OFFSET_DATA_START = 0x1800;    # Same as mine.

* Old version has these addresses (matches Tom's HP1100SeriesConverter, but not mine).

    DATA_OFFSET_FILE_DESC_OLD = 0x005;
    DATA_OFFSET_SAMPLE_INFO_OLD = 0x019;
    DATA_OFFSET_OPERATOR_NAME_OLD = 0x095;
    DATA_OFFSET_DATE_OLD = 0x0B3;
    DATA_OFFSET_METHOD_NAME_OLD = 0x0E5;
    DATA_OFFSET_SIGSTEP_VERSION_OLD = 0x21E;
    DATA_OFFSET_SIGSTEP_SHIFT_OLD = 0x27C;
    DATA_OFFSET_SIGSTEP_STEP_OLD = 0x284;
    DATA_OFFSET_Y_UNITS_OLD = 0x245;
    DATA_OFFSET_DEVSIG_INFO_OLD = 0x255;
    DATA_OFFSET_DATA_START_OLD = 0x400;

* libHPCS also specifically lists ChemStation version "B.06.25" as known,
    c.f. https://github.com/scholer/libHPCS/blob/master/src/libHPCS_p.h#L142



"""

import struct
import numpy as np
# import array

# Magic numbers aka file signatures
# These are listed e.g. here: https://github.com/scholer/libHPCS/blob/master/src/libHPCS_p.h#L116

# MAGIC_BYTES = b'\x03\x31'
# MAGIC_BYTES = b'\x03\x31\x33\x30'

FILE_ADDRS = {
    # Should we also specify the byte-packing format strings here?
    'samplename': 0x35a,
    'operator': 0x758,
    'datestr': 0x957,
    'instrument': 0x9bc,
    'type': 0x9e5,
    'method_name': 0xa0e,
    'software': 0xc10,  # is a struct?  (value is 8)
    'software_name': 0xc11,
    'software_version': 0xe11,
    'software_revision': 0xeda,
    'channel_name': 0x1075,
    'signal_units': 0x104C,
    'signal_stepsize': 0x127c,
    'signal_shift': 0x1274,
    'vwd_data': 0x1800,
    'xmin': 0x11A,
    'xmax': 0x11E,
}

METADATA_KEYS = [
    'samplename', 'operator', 'datestr', 'instrument', 'type', 'method_name',
    'software_name', 'software_version', 'software_revision',
    'channel_name', 'signal_units'
]


def read_str_at_address(f, addr):
    """ Read a binary string at the given file address/offset.

    Args:
        f: File or file-like object.
        addr: The address where the string is located.

    Returns:
        String
    """
    f.seek(addr)
    strlen = int.from_bytes(f.read(1), 'big')
    bytes_be = f.read(strlen * 2)  # We have two characters per
    return bytes_be[::2].decode('utf-8')

    # Alternative, using pascal string format to automatically read :
    # f.seek(addr)
    # buf = f.read(127)
    # buf = buf[0:1] + buf[1:2]  # remove every other byte, because we only use the even ones (?)
    # # buf is now 64 bytes long. We use '64p' as "Pascal string" format to unpack the bytes:
    # return struct.unpack('>64p', buf[0:1] + buf[1:-1:2])[0].decode('utf-8')


def read_agilent_1200_vwd_ch(filename, reset_xmin_xmax=False, time_unit='minutes'):
    """ Read HPLC from Agilent 1200 series variable-wavelength detector (VWD).

    The data is stored in files typically named `vwd1A.ch` or similar.

    Oh my god, this is a terrible data format.
    It sacrifices simplicity for a minor (at most 50%) reduction in file size.
    However, this is at the expense of a much more complex structure,
    where we cannot determine the size of the data without reading every bit of it.
    It would have been much better to just let the user compress the data, if needed.

    I especially don't like that they don't have a pre-defined number of samples,
    because they define xmin/xmax in the datafile, but they don't define neither n_points,
    or sample_rate, so if the data is truncated, it just looks like the data is "stretched out",
    i.e. the sample_rate is lowered (less data points for the duration of the run).

    Args:
        filename:
        reset_xmin_xmax:
        time_unit:

    Returns:
        dict {
            'metadata':
            'timepoints':
            'signal_values':
            'signal_ints':
        }
    """

    with open(filename, 'rb') as f:
        return read_vwd_fh(f, reset_xmin_xmax=reset_xmin_xmax, time_unit=time_unit)


def read_vwd_fh(f, *, reset_xmin_xmax=False, time_unit='minutes'):
    """ Read vwd data from open file or file-like object.

    Args:
        f: Open file.
        reset_xmin_xmax: Generate timepoints with linspace(0.0, total_time, n_datapoints),
            instead of linspace(xmin, xmax, n_datapoints), to mitigate minor differences in
            the start time between runs.
        time_unit: Convert time/index to this unit (minutes or seconds). Passed to `read_xmin_xmax`.

    Returns:
        dict {
            'metadata':
            'timepoints':
            'signal_values':
            'signal_ints':
        }
    """

    metadata = read_metadata(f)  # See METADATA_KEYS

    xmin, xmax = read_xmin_xmax(f, unit=time_unit)
    total_time = xmax - xmin
    print("xmin (minutes):", xmin)
    print("xmax (minutes):", xmax)
    print("total time:    ", total_time)

    # f.seek(FILE_ADDRS['signal_stepsize'])
    signal_stepsize = struct.unpack('>d', file_read(f, FILE_ADDRS['signal_stepsize'], 8))  # double
    signal_shift = struct.unpack('>d', file_read(f, FILE_ADDRS['signal_shift'], 8))  # double
    # signal_shift = 0.0

    print("Signal stepsize:", signal_stepsize)
    print("Signal shift   :", signal_shift)

    # Read integer values from file:
    signal_ints = read_signal_ints(f)

    # Convert integers to float using the file-specified step size:
    signal_values = np.array(signal_ints) * signal_stepsize + signal_shift
    # Any way to get n_datapoints before reading the data? - Nope, don't think so. :-/
    n_datapoints = len(signal_ints)
    sampling_rate = n_datapoints / (total_time * 60)  # In Hz.
    print("n_datapoints:", n_datapoints)
    print("sampling_rate / Hz:", sampling_rate)

    if reset_xmin_xmax:
        # Sometimes the hplc starts at a slight offset for different samples, even for the same method.
        # This is typically insignificant, but it means that the values cannot easily be placed
        # in a single dataframe with a shared index.
        # To mitigate this, you can reset xmin and xmax to 0.0 and total_time instead of xmin/xmax from the instrument:
        timepoints = np.linspace(0.0, total_time, n_datapoints, dtype=float)
    else:
        timepoints = np.linspace(xmin, xmax, n_datapoints, dtype=float)

    # Update metadata:
    metadata['sampling_rate'] = sampling_rate
    metadata['n_datapoints'] = n_datapoints
    metadata['xmin'] = xmin
    metadata['xmax'] = xmax
    metadata['total_time'] = total_time
    metadata['signal_stepsize'] = signal_stepsize
    metadata['signal_shift'] = signal_shift

    return {
        'metadata': metadata,
        'timepoints': timepoints,
        'signal_values': signal_values,
    }


def read_xmin_xmax(f, unit='ms'):
    """ Read time min/max values from file and perform optional conversion.
    The .ch files store time points in milliseconds.
    """
    xmin = int.from_bytes(file_read(f, FILE_ADDRS['xmin'], 4), 'big')
    xmax = int.from_bytes(file_read(f, FILE_ADDRS['xmax'], 4), 'big')
    if unit in ('s', 'seconds'):
        xmin, xmax = xmin/1000., xmax/1000.
    elif unit in ('min', 'minute', 'minutes'):
        xmin, xmax = xmin/60000., xmax/60000.
    elif unit in ('ms', 'milliseconds'):
        xmin, xmax = xmin, xmax
    else:
        raise ValueError("Could not understand unit %r." % unit)

    return xmin, xmax


def read_signal_ints(f, verbose=0):
    """ Read signal integer values from file object.

    VWD .ch data is written primarily as a list of deltas,
    i.e. the difference from one observation to the previous.
    The data is in integers of a signal_stepsize,
    16 bit signed integers (2 bytes) to be precise (so ranging from -32768 to +32768).
    If the delta to the previous value is larger than what can be represented by the 16-bit integer,
    (i.e. larger than 2^15 * signal_stepsize),
    a sentinel value of 0x8000 is used to indicate a large JUMP in the data.
    The next four bytes (64 bits) are then interpreted as a 64-bit int,
    which is the absolute value of the observed signal (but still in integers of signal_stepsize).

    Args:
        f: open file handle or file-like object.
        verbose:

    Returns:
        A list of signal integers for each sample point.
        The integers must be multiplied by signal_stepsize to get the actual y-value.

    """

    f.seek(FILE_ADDRS['vwd_data'])
    idx = 0
    signal_ints = []  # Absolute integer values
    seg_value = 0
    if verbose:
        from collections import Counter
        marker_count = Counter()
        jump_counts = Counter()
    while True:
        addr = f.tell()
        seg_buf = f.read(2)  # A base data segment is two bytes (16 bits)
        if not seg_buf:
            break
        seg_int = int.from_bytes(seg_buf, byteorder='big', signed=True)  # OBS: Is signed.
        # seg_int = struct.unpack('>h', seg_buf)[0]  # Alternative, using struct.unpack.
        if seg_int == -0x8000 or seg_int == 0x8000:
            # 0x8000 is -0x8000 as signed integer (so it reads the same).
            # Special marker value indicating a jump in signal value bigger than what we can express in deltas.
            # (Now we suddenly use 6 bytes in total per data point)
            seg_buf = f.read(4)  # Read a f
            seg_value = int.from_bytes(seg_buf, byteorder='big', signed=True)  # Absolute values are signed!
            if verbose:
                print(f"0x{addr:x}: JUMP to value {seg_value} ! (seg_int == {seg_int})")
                jump_counts[seg_value] += 1
        elif seg_buf[0] == 0x10 and seg_buf[1] != 0x00:
            # 0x10 BIN_MARKER_A, 0x00 BIN_MARKER_END, 0x80 BIN_MARKER_JUMP.
            # There is also something about a marker, at least according to libHPCS,
            # although I'm not quite sure what this means.
            # Known marker values:
            #     102e
            #     104e
            if verbose:
                marker_count[seg_buf] += 1
                print(f"Marker at idx {idx}, address 0x{addr:x} !")
        else:
            seg_value = seg_value + seg_int
            # if seg_int > 0:
            #     print(f"\n seg_int > 0: {seg_int:>10} (seg_buf = {seg_buf.hex()}) \n")
            # print(f"\rIncrementing seg_value by {seg_int:>10} to {seg_value:16}", end='.')
            # print(f"0x{addr:x}: {seg_int:>4x} -> Incrementing seg_value by {seg_int:>8} to {seg_value:16}")
        signal_ints.append(seg_value)
        idx += 1
    if verbose:
        print("Markers:")
        print("\n".join(" - {m:x}: {c}" for m, c in marker_count.items()))
        if verbose >= 2:
            print("JUMPS:")
            print("\n".join(" - {m:x}: {c}" for m, c in jump_counts.items()))
        print("\n - done!")
    return signal_ints


# def read_data_tom(f, stepsize):
#
#     del_ab = stepsize
#     f.seek(FILE_ADDRS['vwd_data'])
#     idx = 0
#     data = []
#
#     while True:
#         f.read(1)  # Always 0x10 ?
#
#         # data point segment read length:
#         rec_len = struct.unpack('>B', f.read(1))[0]
#         if rec_len == 0:
#             break
#
#         for _ in range(rec_len):
#             inp = struct.unpack('>h', f.read(2))[0]  # short
#
#             if inp == -32768:  # 0x8000
#                 inp = struct.unpack('>i', f.read(4))[0]  # int
#                 data.append(inp * del_ab)
#             elif idx == 0:
#                 data.append(inp * del_ab)
#             else:
#                 data.append(data[idx - 1] + inp * del_ab)
#
#             idx += 1


def file_read(f, offset, nbytes):
    if isinstance(offset, str):
        offset = FILE_ADDRS[offset]
    f.seek(offset)
    return f.read(nbytes)


def read_metadata(f):
    metadata = {}
    for k in METADATA_KEYS:
        addr = FILE_ADDRS[k]
        metadata[k] = read_str_at_address(f, addr)
    return metadata






