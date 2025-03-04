import re
import argparse
import time
from cluster import clustering
from log_loader import load_to_dataframe
import logparser
import pandas as pd
import head_compress
from statistics import mode
import os
import math
import py7zr
import numpy as np
from tqdm import tqdm


def extract_variable(variable: np.ndarray, event: str) -> None:
    """extracting variables pattern and save the result

    :param variable: ndarray of messages
    :param event: log event
    :return: None
    """
    variable_list = variable.tolist()
    save = template_path + event  # get template/N1, N2, ... D and so on.

    if len(variable_list[0]) != 0 and event != "D":  # if a variable exists
        temp_df = pd.DataFrame(variable_list)  # create

        for itr in temp_df:
            # {'Jun': 0, 'Jul': 1, 'Aug': 2, 'Sep': 3, 'Oct': 4, 'Nov': 5, 'Dec': 6, 'Jan': 7, 'Feb': 8}
            temp_dict = {
                val1: index for index, val1 in enumerate(temp_df[itr].unique())
            }

            temp_unique = list(temp_dict.keys())  # ['Jun', 'Jul', ...] to list

            temp_digit = True  # to check the column has digits only

            for checker in temp_unique:  # check all values are digits
                if not str(checker).lstrip("-").isdigit():  # any negative also digits
                    temp_digit = False
                    break
                if (
                    int(checker) < -9223372036854775807
                    or int(checker) > 9223372036854775807
                ):  # too large as int -> string variables
                    temp_digit = False
                    break

            if temp_digit:  # this column contains digits only
                time_reg = min(
                    [len(x) for x in temp_unique]
                )  # to find min length for decoding

                d_array = temp_df[itr].to_numpy(
                    dtype="int64"
                )  # (Signed) Int64 stores -9223372036854775807 to 9223372036854775807

                common = mode(
                    d_array
                )  # to calculate (still int32 -> 32 bits = 4 bytes)
                gap = (
                    d_array - common
                )  # many zeros will contain due to mode (still int32)
                bit = 64  # for decoding

                """Change the type to int8, int16, int32, otherwise int64 -> save memory space"""
                if -128 <= gap.min() and gap.max() <= 127:  # 8 bits
                    gap = gap.astype("int8")
                    bit = 8
                elif -32768 <= gap.min() and gap.max() <= 32768:  # 16 bits
                    gap = gap.astype("int16")
                    bit = 16
                elif -2147483648 <= gap.min() and gap.max() <= 2147483647:  # 32 bits
                    gap = gap.astype("int32")
                    bit = 32

                f = open(save + "_Decode_" + str(itr) + ".txt", "w")
                f.write(
                    str(bit) + " " + str(common) + " " + str(time_reg)
                )  # store bit, mode, bit and regex for decoding
                f.close()  # close file

                f = open(
                    save + "_Encode_" + str(itr) + ".txt", "wb"
                )  # write with 8, 16, or 32 bits
                f.write(gap)  # store mode value and bit for decoding
                f.close()  # close file

            else:
                f = open(
                    save + "_Dict_" + str(itr) + ".txt",
                    "w",
                    encoding="ISO-8859-1",
                    errors="ignore",
                )  # template/N1_Dict_0 and so on
                for dict_val in temp_unique:
                    f.write(
                        dict_val + "\n"
                    )  # if None happens -> something error around variables (parse tree)
                f.close()

                # replace dict key from the original values with dict index
                save_np = np.array(
                    [temp_dict[num] for num in temp_df[itr].values]
                ).astype("uint32")
                bit = 32  # to decode

                """Change the type to int8, int16, otherwise, int32 -> save memory space"""
                if save_np.max() <= 255:  # 8 bits
                    save_np = save_np.astype("uint8")
                    bit = 8
                elif save_np.max() <= 4294967295:  # 16 bits
                    save_np = save_np.astype("uint16")
                    bit = 16

                f = open(save + "_Decode_" + str(itr) + ".txt", "w")
                f.write(str(bit))  # store bit for decoding
                f.close()

                f = open(
                    save + "_Encode_" + str(itr) + ".txt", "wb"
                )  # write with 8, 16, or 32 bits
                f.write(save_np)  # store dict index
                f.close()

    elif event == "D":
        f = open(
            template_path + "D.txt", "w", encoding="ISO-8859-1", errors="ignore"
        )  # unicode errors
        for itr in variable_list:
            f.write(str(itr) + "\n")
        f.close()


if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("--InputLog", "-I", help="Input Log File Name")
    parse.add_argument(
        "--SampleRate",
        "-R",
        default=0.01,
        type=float,
        help="Sample rate, default by 0.01",
    )
    parse.add_argument(
        "--HeadLength", "-HL", default="4", help="The designated head length"
    )
    parse.add_argument("--SplitRegex", "-SR", default="\s", help="To Split Head Regex")
    parse.add_argument(
        "--TimeStampRegex", "-TSR", default="\d{2}\:\d{2}\:\d{2}", help="For Timestamp"
    )
    parse.add_argument("--CRound", "-CN", default="5", help="Numer of Clustering round")
    parse.add_argument(
        "--Cluster",
        "-C",
        choices=["HDBSCAN", "DBSCAN", "Mean-Shift", "Affinity-Propagation"],
        default="HDBSCAN",
        help="Clustering method: 'HDBSCAN (Default)', 'DBSCAN', 'Mean-Shift', 'Affinity-Propagation'",
    )

    args = parse.parse_args()

    input_path = args.InputLog
    dataset_name = args.InputLog.split(".")[0]
    template_path = os.path.join(
        f"outputs/{dataset_name}/template/"
    )  # outputs/Log/template
    head_path = os.path.join(f"outputs/{dataset_name}/head/")  # outputs/Log/head
    sample_rate = args.SampleRate
    head_length = int(args.HeadLength)
    split_regex = re.compile(args.SplitRegex)
    time_regex = re.compile(args.TimeStampRegex)
    num_round = int(args.CRound)
    if num_round >= 10 or num_round <= 1:
        print("Use Default 5, Between 1-10")
        num_round = 5

    if not os.path.exists("./outputs"):  # create outputs folder
        os.mkdir("./outputs")
    if not os.path.exists(f"outputs/{dataset_name}"):  # create log folder
        os.mkdir(f"outputs/{dataset_name}")
    if not os.path.exists(template_path):  # create template folder
        os.mkdir(template_path)
    if not os.path.exists(head_path):  # create head folder
        os.mkdir(head_path)

    # collecting Content, Header, and Header Delimiters
    print("Collecting Content and Header From " + args.InputLog)
    heads, content = load_to_dataframe(head_length, split_regex, input_path)

    batch = 100000
    start = 0  # start position
    end = batch  # end position
    if len(heads) < batch:  # if the batch is bigger than input dataset
        end = len(heads)

    current_lap = 0  # current lap
    last_lap = math.ceil(len(heads) / batch)

    # count time
    s_time = time.time()  # start time

    while current_lap < last_lap:
        lap_head = heads[start:end]
        lap_content = np.array(content[start:end])

        # header compression
        head_compress.extract_header(
            lap_head, time_regex, split_regex, head_path, current_lap
        )

        # save split regex
        if current_lap == 0:
            f = open(head_path + "split.info", "w")
            f.write(args.SplitRegex)  # store split regex
            f.close()

        # extract templates
        print("Creating Parser Tree From Samples")
        cluster_start = time.time()
        sample_index = clustering(lap_content, sample_rate, num_round, args.Cluster)
        print("Clustering time cost: {}\n".format(time.time() - cluster_start))

        sample_parser = logparser.LogParser(depth=8, maxChild=100, st=0.1)
        templates, rootNode = sample_parser.parse(
            pd.DataFrame(lap_content[sample_index], columns=["Content"])
        )  # get template and root node
        print("Created Parser Tree From Samples\n")

        # saving templates (dict)
        f = open(template_path + "template.txt", "w")
        f.write(str(templates))
        f.close()
        print("Saved Templates\n")

        # compressing head with 7zip
        with py7zr.SevenZipFile(
            head_path + "head" + str(current_lap) + ".7z", "w"
        ) as head_archive:
            for folder, subfolders, files in os.walk(head_path):
                for file in files:
                    if file.endswith(".txt") or file.endswith(".info"):
                        head_archive.write(
                            os.path.join(folder, file),
                            os.path.relpath(os.path.join(folder, file), head_path),
                        )

        # deleting head files
        del_files = head_path
        for filename in os.listdir(del_files):
            if filename.endswith(".txt") or filename.endswith(".info"):
                os.unlink(os.path.join(del_files, filename))

        # extract templates
        Event = []
        Variable = []
        print("Matching Templates\n")
        for val in tqdm(lap_content):
            logmessageL = sample_parser.preprocess(val)
            matchCluster = sample_parser.treeSearch(rootNode, logmessageL)

            if matchCluster is not None:
                log_template = "".join(matchCluster.logTemplate)

                if val == log_template:  # some log_template does not have <*>
                    Event.append(matchCluster.Nid)
                    Variable.append(val)
                else:  # if template has <*> -> cannot come back with empty variables
                    temp = sample_parser.get_parameter_list(val, log_template)

                    if (
                        not temp
                    ):  # if variables are not found ex) new driver "hiddev" vs new driver "hub"
                        Event.append("D")
                        Variable.append(val)
                    else:  # regular case
                        Event.append(matchCluster.Nid)
                        Variable.append(temp)
            else:
                Event.append("D")  # "D" is dictionary.
                Variable.append(val)

        event_log = pd.DataFrame({"Event": Event})
        event_log["Event"].to_csv(
            template_path + "event.txt", sep=" ", index=False, header=False
        )  # save N1, D, and so on

        # extract variables
        print("Extracting all variables\n")
        for i in tqdm(np.unique(Event)):
            extract_variable(
                np.array(Variable, dtype=object)[np.where(np.array(Event) == i)[0]], i
            )

        # compressing template with 7zip
        with py7zr.SevenZipFile(
            template_path + "content" + str(current_lap) + ".7z", "w"
        ) as template_archive:
            for folder, subfolders, files in os.walk(template_path):
                for file in files:
                    if file.endswith(".txt"):
                        template_archive.write(
                            os.path.join(folder, file),
                            os.path.relpath(os.path.join(folder, file), template_path),
                        )

        # deleting template files
        del_files = template_path
        for filename in os.listdir(del_files):
            if filename.endswith(".txt"):
                os.unlink(os.path.join(del_files, filename))

        # this if for while loop and next round
        print("Current Lap is: ", current_lap + 1, "Final Lap is: ", last_lap)

        start = end  # get the next start position
        end += batch  # get new end point = current end + batch
        if end >= len(heads):  # if the end is over the input dataset
            end = len(heads)  # the last location is end of the dataset
        current_lap += 1
        # end of while

    e_time = time.time()
    print("Total time cost: {}".format(e_time - s_time))

    # calculating compress rate: original / compressed files
    head = head_path
    size = 0
    for filename in os.listdir(head):
        if filename.endswith(".7z"):
            size += os.path.getsize(os.path.join(head, filename))

    template = template_path
    for filename in os.listdir(template):
        if filename.endswith(".7z"):
            size += os.path.getsize(os.path.join(template, filename))

    original_size = os.path.getsize(input_path)

    print(f"{dataset_name}: Compression Rate is :", (original_size / size))
