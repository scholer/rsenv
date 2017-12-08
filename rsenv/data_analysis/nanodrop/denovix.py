

import csv
import numpy as np
import pandas as pd


def str_arr_to_int(str_arr):
    # return [int(v) for v in str_arr]
    return np.array(str_arr, dtype=np.int)


def str_arr_to_float(str_arr):
    # return [float(v) for v in str_arr]
    return np.array(str_arr, dtype=np.float)


def str_is_int(s):
    try:
        v = int(s)
    except ValueError:
        return False
    else:
        return True


def csv_to_dataframe(filename, header_fmt="{Sample Name}-{Sample Number}", values_start_idx=24, include_only=None):
    """Create a Pandas DataFrame from Denovix csv export file.
    
    Args:
        filename: 
        header_fmt: 
        values_start_idx: Which column the measurement values begin at. For current Denovix software, this is 24.

    Returns:
        2-tuple of (dataframe, metadata)

    """

    # Using Pandas?
    # csv_data = pd.read_csv(filename)
    # x_index = csv_data.columns.values[csv_data]

    # Or just use csv module directly?
    with open(filename) as fd:
        csvreader = csv.reader(fd)  # , delimiter=',', quotechar='"')
        header = next(csvreader)
        # sample_num_hdr_idx = header.index('Sample Number')
        # sample_name_hdr_idx = header.index('Sample Name')
        # datetime_hdr_idx = header.index('Sample Name')
        if values_start_idx is None:
            values_start_idx = next(idx for idx, fieldname in enumerate(header) if str_is_int(fieldname))
        x_vals = str_arr_to_int(header[values_start_idx:])
        # measurements = [{
        #     'metadata': dict(*zip(header[:values_start_idx], row[:values_start_idx])),
        #     'y_vals': str_arr_to_int(row[values_start_idx:])
        #    } for row in csvreader]
        metadata, y_vals = zip(*[
            (dict(zip(header[:values_start_idx], row[:values_start_idx])), str_arr_to_float(row[values_start_idx:]))
            for num, row in enumerate(csvreader) if include_only is None or num in include_only
        ])
    print("len(y_vals):", len(y_vals))
    print("len(metadata):", len(metadata))

    # Let's just assume unique column names:
    # data = {header_fmt.format(**m['metadata']): m['y_vals'] for m in measurements}
    # df = pd.DataFrame(data=data, index=x_vals)
    # # alternatively:
    # df = pd.DataFrame(data=[m['y_vals'] for m in measurements],
    #                   columns=[header_fmt.format(**m['metadata']) for m in measurements],
    #                   index=x_vals)
    # Edit: Column names (indices in general) do not have to be unique.
    # And the user may actually want to have identically named columns.
    columns = [header_fmt.format(**m) for m in metadata]
    print("len(columns):", len(columns))
    print("len(x_vals):", len(x_vals))

    # data is a list of columns, each column matching up with index, so orient must be 'index' (default: 'columns').
    # df = pd.DataFrame(data=y_vals, columns=columns, index=x_vals, orient='index')
    # However, DataFrame.__init__ doesn't support 'orient' keyword, and from_item constructor doesn't support index keyword.
    # df = pd.DataFrame.from_items(items=y_vals, columns=columns, index=x_vals, orient='index')
    # Sigh. Just convert y_vals to numpy array and transpose:
    y_vals = np.array(y_vals)
    print("y_vals.shape", y_vals.shape)
    df = pd.DataFrame(data=y_vals.T, columns=columns, index=x_vals)

    # if isinstance(metadata, list):
    #     if not keep_yvals:
    #         for d in measurements:
    #             d.pop('y_vals')
    #     metadata.extend[measurements]
    return df, metadata
