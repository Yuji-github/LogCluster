import numpy as np
import pandas as pd
import glob
from time_stamp_decompress import time_decompress
from tqdm import tqdm


def decompress(head_path:str, timestamp_regex:str) -> pd.DataFrame:
    """decompress head file

    :param head_path: zipped head file path
    :param timestamp_regex: regex pattern for timestamp
    :return: pd.DataFrame of header
    """
    files = [
        file for file in glob.glob(head_path + "H_Decode*.txt")
    ]  # read decoding file
    files = sorted(files)
    num = 0
    head = pd.DataFrame()  # to store the value
    time = False  # check this header contains timestamp
    time_num = 0  # what column is timestamped
    strip_word = head_path[:-1] + "\\H_Decode.txt"
    for file_name in files:

        if num != int(
            file_name.strip(strip_word)
        ):  # assume num = 5 and reading H_Decode6
            head[str(num)] = " "  # adding empty
            num += 1

        file = open(file_name, "r", encoding="ISO-8859-1", errors="ignore")
        bit = file.readlines()  # extract bit and mode values
        file.close()
        info = np.asarray(
            [val.split(" ") for val in bit]
        ).flatten()  # first value is bit, second is mode

        decode = ""  # for decoding
        if (
            len(info) == 1
        ):  # this column has variables -> dictionary decoding (uint = no negative dut to index number)
            if int(info[0]) == 8:
                decode = "uint8"
            elif int(info[0]) == 16:
                decode = "uint16"
            else:
                decode = "uint32"

            """Reading Encode and Dictionary Files: *decode type is the most important otherwise it doesn't work"""
            encode = head_path + "H_Encode" + str(num) + ".txt"
            index = np.fromfile(encode, dtype=decode)  # read every 8, 16 or 32 bits

            d = head_path + "H_Dict" + str(num) + ".txt"
            f = open(d, "r", encoding="ISO-8859-1", errors="ignore")
            this_dict = f.readlines()  # extract dictionary values
            f.close()

            value = []
            for idx in index:
                temp = this_dict[int(idx)]
                if temp.strip() == "t":  # 't' is timestamp: 't' is in Dict
                    time = True  # found timestamp
                    time_num = num  # this column has a timestamp

                restore = temp.strip()
                if (
                    restore != "" and "-" in restore[0] and len(restore) > 1
                ):  # if negative has it, -> replace to a space
                    restore = restore.replace("-", " ")
                value.append(
                    restore
                )  # remove \n because split values might be different

            head[str(num)] = value  # add values to df

        if (
            len(info) == 2
        ):  # this column has digits -> calculate original with mode (int = negative include)
            if int(info[0]) == 8:
                decode = "int8"
            elif int(info[0]) == 16:
                decode = "int16"
            else:
                decode = "int32"

            mode = int(info[1])  # this value is important for decoding

            """Reading Encode Only *decode type is the most important otherwise it doesn't work"""
            encode = head_path + "H_Encode" + str(num) + ".txt"
            gap = np.fromfile(encode, dtype=decode)  # read every 8, 16 or 32 bits

            original = (
                gap + mode
            )  # assume there is no negative values: if negative -> original was a space
            original = list(
                map(str, original)
            )  # check no negative (-): if (-) includes (-) -> ' ' space

            for itr, val in enumerate(original):
                if "-" in val:  # if negative has it, -> replace to a space
                    original[itr] = val.replace("-", " ")

            head[str(num)] = original  # add values to df

        num += 1

    if time:  # if timestamp 't' is contained,
        timestamp = time_decompress(
            head_path, timestamp_regex
        )  # return list: some rows do not have a timestamp
        time_idx = 0  # to skip not timestamp row

        print("\nReplacing Timestamps")
        for idx, val in tqdm(enumerate(head.iloc[:, time_num].values)):
            if val == "t":  # if this is time stamp
                head.iloc[idx, time_num] = timestamp[time_idx]  # replace
                time_idx += 1

    return head
