import numpy as np
import glob
import re
import ast
from tkinter import Tcl
import os
from tqdm import tqdm


def content_decompress(template_path):
    """Replace Templates and Not Templates"""
    # get event for templates
    e = open(template_path + "event.txt", "r", encoding="ISO-8859-1", errors="ignore")
    event = e.readlines()  # get event data
    e.close()
    event = [idx.strip() for idx in event]  # remove \n

    # convert to numpy
    event = np.array(event).astype(
        dtype="object"
    )  # must have dtype='object' to replace values
    content = np.empty(
        len(event), dtype="object"
    )  # # must have dtype='object' to replace values

    # get templates
    t = open(
        template_path + "template.txt", "r", encoding="ISO-8859-1", errors="ignore"
    )
    template = t.readlines()  # get templates (string)
    t.close()

    # add templates based on event values
    template_dict = ast.literal_eval(template[0])  # convert to dict type

    for key, value in template_dict.items():  # create template column with dict
        content[event == key] = value

    # get D values: not in the template
    if os.path.exists(template_path + "D.txt"):
        i = open(template_path + "D.txt", "r", encoding="ISO-8859-1", errors="ignore")
        d = i.readlines()  # get D
        i.close()

        # replace D (event) to saved values
        content[event == "D"] = d

    """ Replace Variables """
    lists = [
        file for file in glob.glob(template_path + "N*_Decode_*.txt")
    ]  # read decoding file
    files = Tcl().call("lsort", "-dict", lists)  # sort files

    # files have N*_Decode_0, N*_Decode_1  :assume * is the sane number, but 0 comes first -> if not replace does not work
    for file in tqdm(files):
        f = open(file, "r")
        values = f.readlines()  # extract bit and mode values
        f.close()
        info = np.asarray(
            [val.split(" ") for val in values]
        ).flatten()  # first value is bit, second is mode, third regex

        # N11_Decode_0.txt -> read N11_Encode_0.txt and N11_Dict_0.txt
        num_arr = re.findall("\d+", file)  # store digits from the file ['7', '0']
        n_num = num_arr[0]  # get N number N7 -> 7 (string)
        en_num = num_arr[1]  # get encode number _0 -> 0 (string)
        target_event = "N" + n_num  # N1, N2, and so on

        decode = ""  # for decoding
        if (
            len(info) == 1
        ):  # variables -> dictionary decoding (uint = no negative dut to index number)
            if int(info[0]) == 8:
                decode = "uint8"
            elif int(info[0]) == 16:
                decode = "uint16"
            else:
                decode = "uint32"

            """Reading Encode and Dictionary Files: *decode type is the most important otherwise it doesn't work"""
            encode = template_path + "N" + n_num + "_Encode_" + en_num + ".txt"
            index = np.fromfile(encode, dtype=decode)  # read every 8, 16 or 32 bits

            content_dict = template_path + "N" + n_num + "_Dict_" + en_num + ".txt"
            fc = open(content_dict, "r", encoding="ISO-8859-1", errors="ignore")
            this_dict = fc.readlines()  # extract dictionary values
            fc.close()

            value = []
            for idx in index:
                temp = this_dict[int(idx)]
                value.append(
                    temp.strip()
                )  # remove \n because split values might be different

            # replace <*> from top : templates have multiple variables <*> <*>
            group = np.where(event == target_event)[0]
            for idx, np_idx in enumerate(group):
                content[np_idx] = str(
                    np.char.replace(content[np_idx], "<*>", value[idx], count=1)
                )

        elif (
            len(info) > 1
        ):  # variables are numerical -> calculate original with mode (int = negative include)
            if int(info[0]) == 8:
                decode = "int8"
            elif int(info[0]) == 16:
                decode = "int16"
            elif int(info[0]) == 32:
                decode = "int32"
            else:  # compression phase int64 is default
                decode = "int64"

            mode = int(info[1])  # this value is important for decoding
            digit_num = int(
                info[2]
            )  # original: min length "01" = 2  -> info[2] string -> int 2

            """Reading Encode Only *decode type is the most important otherwise it doesn't work"""
            encode = template_path + "N" + n_num + "_Encode_" + en_num + ".txt"
            gap = np.fromfile(encode, dtype=decode)  # read every 8, 16, 32, or 64 bits

            original = gap + mode
            original = list(map(str, original))
            """
            original has [001]  -> encode -> [1]: missing 00 
            regex will be \d{3} -> 3 digits needs 
            (original 3 digits - current 1 digit) -> "0" * (3 - 1) -> 00
            get back 001
            """
            for itr, val in enumerate(original):
                if len(val) < digit_num:  # 1 < 01
                    miss_zero = "0" * (digit_num - len(val))  # missing values are 0's
                    original[itr] = miss_zero + original[itr]

            # replace <*> from top : templates have multiple variables <*> <*>

            group = np.where(event == target_event)[0]
            for idx, np_idx in enumerate(group):
                content[np_idx] = str(
                    np.char.replace(content[np_idx], "<*>", original[idx], count=1)
                )

    return content
