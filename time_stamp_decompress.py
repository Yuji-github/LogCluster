import numpy as np
import pandas as pd
import glob
import re
from typing import List
sep_val = 0

def time_decompress(head_path: str, timestamp_regex: str) -> List:
    """decompress timestamp

    :param head_path: head path
    :param timestamp_regex: regex (str)
    :return: list of timestamps
    """

    files = [
        file for file in glob.glob(head_path + "t_Decoding*.txt")
    ]  # read decoding file
    files = sorted(files)
    num = 0
    time_df = pd.DataFrame()  # to store the value
    digit_num = re.findall(
        "\d+", timestamp_regex
    )  # \d{2}\:\d{2}\:\d{2} -> ['2', '2', '2']
    sep = re.findall(
        "[\-\:\,\.\]]", timestamp_regex
    )  # \d{2}\:\d{2}\:\d{2}\,\d{3} -> [':', ':', ',']

    for file_name in files:
        file = open(file_name, "r")
        values = file.readlines()  # extract bit and mode values
        file.close()
        info = np.asarray([val.split(" ") for val in values]).flatten()

        # encoded timestamp will contain negative -> (signed) int
        bit = int(info[0])  # for reading files
        mode = int(info[1])  # for calculate original values
        decode = "int32"  # default

        if bit == 8:
            decode = "int8"
        elif int(info[0]) == 16:
            decode = "int16"

        """Reading Encode Only *decode type is the most important otherwise it doesn't work"""
        encode = head_path + "t_Encode" + str(num) + ".txt"
        gap = np.fromfile(encode, dtype=decode)  # read every 8, 16 or 32 bits

        original = (
            gap + mode
        )  # assume there is no negative values: if negative -> original was a space
        original = list(
            map(str, original)
        )  # check some values have 1 digit, but original has 2 digits (1 vs 01)

        """
        original (milliseconds) has [001]  -> encode -> [1]: missing 00 
        regex will be \d{3} -> 3 digits needs 
        (original 3 digits - current 1 digit) -> "0" * (3 - 1) -> 00
        get back 001
        """
        for itr, val in enumerate(original):
            if len(val) != int(digit_num[num]):
                miss_zero = "0" * (
                    int(digit_num[num]) - len(val)
                )  # missing values are 0's
                original[itr] = miss_zero + original[itr]

        time_df[str(num)] = original  # add values to df
        num += 1

    # convert to timestamp form
    timestamp = []

    for itr in time_df.iterrows():  # iterate each rows
        temp = ''  # to store values (string)

        for idx in range(len(itr[1]) - 1):  # sep is always len(row)-1
            temp += itr[1][idx] + sep[idx]  # add all seps, but missing the last values -> 01:12:

        temp += itr[1][-1]  # add the last value here -> 01:12:23
        timestamp.append(temp)  # append the value

    return timestamp
