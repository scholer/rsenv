

"""

From https://github.com/TheTrueTom/HP1100SeriesConverter

License: MIT License.

Note: This is for an older version of ChemStation than the one we have, so it doesn't work for our data files.

"""


import os
import struct
import csv

MAGIC_BYTE = b'\x02\x33'


def read_ind_file(fname):

    print("Reading HP1100 file:", fname)

    with open(fname, 'rb') as f:

        file_byte_marker = f.read(2)

        if file_byte_marker != MAGIC_BYTE:
            print(f" - ERROR: Invalid file! File should begin with {MAGIC_BYTE!r},"
                  f" actual byte marker is {file_byte_marker!r}.")
            return

        infos = []

        f.seek(0x18)  # 24th byte
        # Could also use int.from_bytes(f.read(1), 'big') instead of struct.unpack(...)[0].
        sample = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(sample)

        f.seek(0x94)
        operator = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(operator)

        f.seek(0xB2)
        date = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(date)

        f.seek(0xD0)
        weird1 = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(weird1)

        f.seek(0xDA)
        weird2 = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(weird2)

        f.seek(0xE4)
        method = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(method)

        f.seek(0x195)
        version = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(version)

        f.seek(0x244)
        yUnits = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(yUnits)

        f.seek(0x254)
        detector = str(f.read(struct.unpack('>B', f.read(1))[0]))  # unsigned char
        infos.append(detector)

        f.seek(0x284)
        del_ab = struct.unpack('>d', f.read(8))[0]  # double

        f.seek(0x400)
        loc = 0
        data = []

        while True:
            f.read(1)  # Always 0x10 ?

            rec_len = struct.unpack('>B', f.read(1))[0]
            if rec_len == 0:
                break

            for _ in range(rec_len):
                inp = struct.unpack('>h', f.read(2))[0]  # short

                if inp == -32768:  # 0x8000
                    inp = struct.unpack('>i', f.read(4))[0]  # int
                    data.append(inp * del_ab)
                elif loc == 0:
                    data.append(inp * del_ab)
                else:
                    data.append(data[loc - 1] + inp * del_ab)

                loc += 1

        # Time points generation (x axis) / Temps de début et de fin en ms
        f.seek(0x11A)
        st_t = struct.unpack('>i', f.read(4))[0]
        en_t = struct.unpack('>i', f.read(4))[0]

        data_len = len(data)
        interval = (en_t - st_t) / data_len
        times = []
        loc2 = 0

        for _ in range(data_len):
            if len(times) == 0:
                times.append(st_t)
            else:
                times.append(times[loc2 - 1] + interval)

            loc2 += 1

    for i in range(len(infos)):
        infos[i] = infos[i].replace(',', ' -')  # Avoid commas in infos (replace them with -)

    print(" - done!")

    return infos, times, data

