from re import Pattern
from typing import Tuple


def load_to_dataframe(
    head_length: int, split_regex: Pattern, input_path: str
) -> Tuple[list, list]:
    """load log file and split log data into header and messages

    :param head_length: length of log header
    :param split_regex: regex pattern to split log file
    :param input_path: path to input log file
    :return: heads, messages
    """
    # import data
    file = open(input_path, "r", encoding="ISO-8859-1", errors="ignore")
    lines = file.readlines()

    # Preparation
    headers = []
    log_messages = []

    for line in lines:
        h = True
        line = line.replace("\t", r"\t")
        temp = split_regex.split(
            line
        )  # ex) split by \s -> ['Jun', '', '9', '06:06:20', ...]
        copy_temp = temp.copy()  # store actual values
        if len(set(temp)) == 1 and next(iter(set(temp))) == "":  # the line is empty
            headers.append("\s " * head_length)
            h = False

        start = 0  # to stop for header
        head = ""
        remove = ""  # to remove = store pure values
        space = " "
        if split_regex.pattern[-1] != "s":
            space = split_regex.pattern[-1]

        if h:
            head_num = len(headers)
            for idx, val in enumerate(temp):  # extract headers
                remove += copy_temp[idx] + space  # store actual values

                if val != "":  # regular values
                    head += str(val) + space  # append values with a space
                    start += 1

                else:  # if val is '' -> do not add to head
                    if idx < (len(temp) - 1):  # not the last position
                        if temp[idx + 1].isdigit():  # do not add to head
                            temp[idx + 1] = (
                                int(temp[idx + 1]) * -1
                            )  # assume header does not have any negative values
                        else:
                            temp[idx + 1] = "\s" + temp[idx + 1]  # add to the space

                if head_length == start:  # until here is a header
                    headers.append(head)
                    break  # leftovers are going to a content

            if head_num == len(headers):  # no added
                headers.append("\s " * head_length)

        temp_content = line.replace(remove, "")  # leftovers are for content
        content = split_regex.split(temp_content)  # split
        final_content = ""  # to store

        for idx, val in enumerate(content):
            if val == "" and idx < (len(content) - 1):
                content[idx] = "\s"  # replace \s

            if idx <= (len(content) - 1):  # without \n
                if idx == (len(content) - 1):  # last
                    final_content += content[idx]
                else:  # regular
                    final_content += content[idx] + " "

        if final_content == head:
            headers[-1] = "\s " * head_length

        log_messages.append(final_content.strip())

    print("Total lines {}".format(len(lines)))

    return headers, log_messages
