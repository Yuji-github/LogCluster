from head_decompress import decompress
from content_decompress import content_decompress
import argparse
import py7zr
import os
from tqdm import tqdm
from tkinter import Tcl


def __path_pro(path:str) -> str:
    """adding / at the end of path
    :param path: path
    :return: path with / at the end
    """
    if path[-1] != "/":
        path += "/"
    return path


if __name__ == "__main__":  # main
    parse = argparse.ArgumentParser()
    parse.add_argument("--DecompressLog", "-DL", help="Decompress Log Folder Name")

    args = parse.parse_args()
    dataset_name = (
        args.DecompressLog.split(".")[0]
        if "." in args.DecompressLog
        else args.DecompressLog
    )
    template_path = __path_pro(
        f"outputs/{dataset_name}/template"
    )  # adding '/' at the last
    head_path = __path_pro(
        f"outputs/{dataset_name}/head"
    )  # adding '/' at the last

    # if no path to extract -> exit
    if not os.path.exists(head_path):
        print("There is no path to extract headers")
        exit()
    if not os.path.exists(template_path):
        print("There is no path to extract templates")
        exit()
    if not os.path.exists("outputs"):  # create output folder
        print("Output Folder Is Creating")
        os.mkdir("outputs")

    """Get Header and Content File Names"""
    head_file = []
    for folder, subfolders, files in os.walk(head_path):
        for file in files:
            if file.endswith(".7z"):
                head_file.append(os.path.join(folder, file))  # get header files
    head_file = Tcl().call("lsort", "-dict", head_file)  # sort

    content_file = []
    for folder, subfolders, files in os.walk(template_path):
        for file in files:
            if file.endswith(".7z"):
                content_file.append(os.path.join(folder, file))  # get content files
    content_file = Tcl().call("lsort", "-dict", content_file)  # sort

    # extract
    split_regex = ""  # for split regex
    timestamp_regex = ""  # for timestamp regex

    print("Extracting Start: This Process Takes A Lot Of Time")
    for itr in range(len(head_file)):  # head and content have the same numbers of files
        """Head Part"""
        # extract archives
        head_archive = py7zr.SevenZipFile(head_file[itr], mode="r")  # read
        head_archive.extractall(path=head_path)  # extract head files

        if itr == 0:  # if this is the first time
            if os.path.exists(head_path + "Timestamp_reg.info"):
                time = open(
                    head_path + "Timestamp_reg.info", "r"
                )  # for timestamp regex
                timestamp_regex = time.readlines()[
                    0
                ]  # assume timestamp has only 1 item ex) \d{2}\:\d{2}\:\d{2}
                time.close()

            split = open(head_path + "split.info", "r")
            split_regex = split.readlines()[0]  # assume split regex looks \s, \|
            split.close()

        print("Decompress " + head_file[itr])
        head = decompress(head_path, timestamp_regex)

        # deleting head files
        del_files = head_path
        for filename in os.listdir(del_files):
            if filename.endswith(".txt"):
                os.unlink(os.path.join(del_files, filename))

        """Content Part"""
        # extract archives
        content_archive = py7zr.SevenZipFile(content_file[itr], mode="r")  # read
        content_archive.extractall(path=template_path)  # extract content files

        print("Decompress " + content_file[itr])
        content = content_decompress(template_path)

        # deleting content files
        del_files = template_path
        for filename in os.listdir(del_files):
            if filename.endswith(".txt"):
                os.unlink(os.path.join(del_files, filename))

        # write the file to output
        head_list = head.values.tolist()  # convert this head (df) to list
        content_list = content.tolist()

        temp_out = []  # store the values here

        print("\nFinal Checking")
        for idx in tqdm(range(len(head_list))):  # both have the same length
            temp_line = ""  # this value going to temp_out

            for col in range(len(head_list[idx])):  # header needs to add only
                head_temp = str(head_list[idx][col])  # to store this value

                if r"\t" in head_temp:
                    head_temp = head_temp.replace(r"\t", "\t")

                if "\s" in head_temp:  # if current has \s -> replace
                    if "\s" in split_regex:  # split_regex is string
                        head_temp = head_temp.replace("\s", " ")
                    else:
                        sep = split_regex.replace(
                            "\\", ""
                        )  # assume \, -> ['|'] <class 'str'>  : split is always third position
                        head_temp = head_temp.replace(
                            "\s", sep
                        )  # sep = | assume split is always 1 char such as bar |, commna,  period.

                if split_regex == "\s":
                    temp_line += head_temp + " "
                else:
                    sep = split_regex.replace("\\", "")  # assume \, -> ,
                    temp_line += head_temp + sep

            # if content contain '\s'
            content_temp = str(content_list[idx])

            if r"\t" in content_temp:
                content_temp = content_temp.replace(r"\t", "\t")

            if "\s" in content_temp:
                if "\s" in split_regex:
                    content_temp = content_temp.replace("\s", "")
                else:
                    sep = split_regex.replace("\\", "")  # assume \, ->
                    content_temp = content_temp.replace("\s", sep)  # assume \, -> ,

            if "\n" in content_temp:
                content_temp = content_temp.replace("\n", "")  # remove \n

            temp_line += content_temp  # add content value (assume already 1 line)

            temp_out.append(temp_line)

        # end of for loop

        # save this output
        print("\nWriting The File to Output Folder\n")
        f = open(
            "./outputs/" + str(itr) + ".txt",
            "w",
            encoding="ISO-8859-1",
            errors="ignore",
        )
        for val in temp_out:
            f.write(str(val) + "\n")
        f.close()

    # end of big for loop

    # deleting regex files: assume the regex files are located a header folder
    del_files = head_path
    for filename in os.listdir(del_files):
        if filename.endswith(".info"):
            os.unlink(os.path.join(del_files, filename))

    # concatenate multiple files
    if len(head_file) > 1:  # multiple files
        # get file names
        output_files = []
        for folder, subfolders, files in os.walk("outputs/"):
            for file in files:
                if file.endswith(".txt"):
                    output_files.append(os.path.join(folder, file))  # get out_out files

        output_files = Tcl().call("lsort", "-dict", output_files)  # sort

        # concatenate the files
        with open(
            "./outputs/output.log", "w", encoding="ISO-8859-1", errors="ignore"
        ) as outfile:
            for fname in output_files:
                with open(fname, encoding="ISO-8859-1", errors="ignore") as infile:
                    for line in infile:
                        outfile.write(line)

    print("Finished Decompression")
