import argparse
import os
from difflib import SequenceMatcher

if __name__ == "__main__":  # main
    parse = argparse.ArgumentParser()

    parse.add_argument("--Original", "-O", help="Original Txt data")
    parse.add_argument("--Decompress", "-D", help="Decompressed Txt data")

    args = parse.parse_args()
    file_A = str(args.Original)
    file_B = str(args.Decompress)

    if not os.path.exists(file_A) or not os.path.exists(file_B):
        print("There is no path to compare")
        exit()

    score = 0
    total_line = 0

    with open(file_A, encoding="ISO-8859-1", errors="ignore") as A, open(
        file_B, encoding="ISO-8859-1", errors="ignore"
    ) as B:
        while True:
            a, b = A.readline(), B.readline()
            if not a:
                break
            score += SequenceMatcher(None, a, b).ratio()
            total_line += 1
    print("Read Lines: {0}".format(total_line))
    print("Lossless Score : {:.2f} %".format((score / total_line) * 100))
