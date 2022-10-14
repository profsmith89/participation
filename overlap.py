""" overlap.py: Given two CSV files of Perusall annotations, build a
    dictionary of document titles that indicates to which year a
    document belongs. The answer is year1-only, year2-only, or
    both years.
Author: Mike Smith
Date:   20210903
"""

import sys
import csv

"""Expected format of input Perusall-annotation CSV files
0: Last name, 1: First name, 2: Student ID
3: Submission -- the actual text of the annotation
4: Type -- {comment, question}
5: Score -- [0-2]
6: Created, 7: Last edited at -- date time format
8: Replies, 9: Upvoters
10: Status -- ???
11: Document, 12: Page number
13: Range -- description of annotation anchor {text, rectangle} in document
"""

# Dictionaries built for each dataset in files
dicts = []

def overlap(files):
    """Compute the overlap across two years in documents used

    Input:   A list of exactly two filenames
    Output:  A dictionary of document titles. The value of each dictionary
             is year1, year2, or `'both'`.
    Assumes: The name of a file without its `.csv` extension is a year
             (e.g., 2021).
    """
    assert(len(files) == 2)

    docs = {}

    # Process the first input file. It's easy because every unique
    # document is just associated by default with this first year.
    fname = files[0]
    yr1 = fname.split('.')[0]

    with open(f'annotations/{fname}') as fin:
        csv_reader = csv.reader(fin, delimiter=',')
        line = 0

        for row in csv_reader:
            if line != 0:    # skipping header row
                docs[row[11]] = yr1
            line += 1

        print(f'Processed {line} lines in {fname}')
    print(f'{len(docs)} documents in {yr1}')

    # Process the second input file. A little tricker since we have
    # to notice actual overlaps.
    fname = files[1]
    yr2 = fname.split('.')[0]

    with open(f'annotations/{fname}') as fin:
        csv_reader = csv.reader(fin, delimiter=',')
        line = 0

        for row in csv_reader:
            if line != 0:    # skipping header row
                doc = row[11]
                if docs.get(doc) == None:
                    # First time we've seen this title
                    docs[doc] = yr2
                elif docs.get(doc) != yr2:
                    # Might be other year or "both", but in any case, write "both"
                    docs[doc] = 'both'
                # else already recorded that it's just in this year
            line += 1

        print(f'Processed {line} lines in {yr2}')

    cnt_yr2 = 0
    cnt_overlap = 0
    for doc in docs:
        if docs.get(doc) == yr2:
            cnt_yr2 += 1
        if docs.get(doc) == 'both':
            cnt_yr2 += 1
            cnt_overlap += 1
    print(f'{cnt_yr2} documents in {yr2}')
    print(f'{cnt_overlap} documents in both years')

    return docs


def main():
    files = []

    if len(sys.argv) != 3:
        sys.exit('Usage: python3 overlap.py [year1].csv [year2].csv')
    files.append(sys.argv[1])
    files.append(sys.argv[2])

    docs = overlap(files)

    print('In what year does a document appear?')
    for doc in docs:
        print(f'{docs[doc]}: {doc}')

if __name__ == '__main__':
    main()