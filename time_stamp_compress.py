import pandas as pd
import re
from itertools import groupby
from statistics import mode


def __find_regex(line: str) -> str:
    """find regex pattern of time stamp

    :param line: sample of time stamp
    :return: regex pattern of time stamp
    """
    regex = []
    for char in line:
        if char.isdigit():  # if char is digit, then add as 'd'
            regex.append("d")
        elif bool(
            re.search("[a-zA-Z]", char)
        ):  # any string characters from A-Z (including lower cases)
            regex.append("w")
        else:  # special characters such as [ ? > { :
            regex.append(char)

    grp = groupby(regex)
    return "".join(
        f"\\{what}{{{how_many}}}" if how_many > 1 else f"\\{what}"
        for what, how_many in ((g[0], len(list(g[1]))) for g in grp)
    )


def time_compress(data: list, head_path: str, num: int) -> None:
    """compress time stamp

    :param data: list of time stamp
    :param head_path: head path
    :param num: compress num
    :return: None
    """
    # data = ["12:12:01,400"] re.split(r'[-:,.]', time)
    if num == 0:  # Store the regex for decoding: 1 regex is enough
        time_reg = __find_regex(
            str(data[0])
        )  # always the first item is store as the original value
        f = open(head_path + "Timestamp_reg.info", "w")
        f.write(time_reg)  # store mode value and bit for decoding
        f.close()  # close file

    # split timestamp -> year, month, day, hour, minute, second, millisecond * year, month and day are super rare but possible
    time = []
    for itr in data:  #  r'[-:,.]'
        temp = re.split(
            r"\D", itr
        )  # split any -:,. values -> this separates year, month, day, hour, minute, second and millisecond
        time.append(list(filter(None, temp)))  # drop any None values

    time_df = pd.DataFrame(time)  # create timestamp_df

    """Differentiate each column with mode"""
    for itr in time_df:
        time_array = time_df[itr].to_numpy(
            dtype="int32"
        )  # (Signed) Int32 -> -2,147,483,648 to 2,147,483,647 (all time is positive, but later might be negative.)
        common = mode(time_array)  # to store mode value for decoding
        gap = time_array - common  # many zeros will contain due to mode (still int32)
        bit = 32  # for decoding

        """Change the type to int8, int16, otherwise, int32 -> save memory space"""
        if -128 <= gap.min() and gap.max() <= 127:  # 8 bits
            gap = gap.astype("int8")
            bit = 8
        elif -32768 <= gap.min() and gap.max() <= 32768:  # 16 bits
            gap = gap.astype("int16")
            bit = 16

        save = head_path + "t_Decoding" + str(itr)
        f = open(save + ".txt", "w")
        f.write(str(bit) + " " + str(common))  # store bit and mode for decoding
        f.close()

        save = head_path + "t_Encode" + str(itr)
        f = open(save + ".txt", "wb")  # write with 8, 16, or 32 bits
        f.write(gap)  # store dict index
        f.close()
