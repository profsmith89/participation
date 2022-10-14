"""tenpc.py: Creates files for inter-coder reliability testing

We create a to-be-coded (tbcoded) CSV file for hand-coding a percentage of the
randomized dataset of Perusall annotations.  This routine simultaneously creates
an already-coded version (arcoded) of the all-years files in the same format as
the tbcoded file.

Author: Mike Smith Date:   20211123
"""

import sys
import csv

"""Format of the randomized Perusall-annotation CSV files
--- Fields in `all-years` CSV file ---
0: Reply [0 if comment is not; 1 if it is]
1: Submission -- the actual text of the annotation

--- Fields in `all-years.key` CSV file ---
0: Year
1: Student ID
2: Replies
3: Upvoters
4: Document
5: Authentic? -- coding field
6: Rich discussion? -- coding field

--- Fields in `tbcoded` and `arcoded` CSV files ---
0: Conversation ID
1: Authentic? -- coding field
2: Rich discussion? -- coding field
3: Comment -- the actual text of the student's comment
"""

###
### Global variables
###

FNAME_DATA = 'annotations/all-years.csv'
FNAME_KEY = 'annotations/all-years.key.csv'
FNAME_TBNEW = 'annotations/tbcoded.csv'
FNAME_ARNEW = 'annotations/arcoded.csv'

PERCENT_GRABBED = 10

# Where we collect the new file data
new_tbdata = []
new_ardata = []

###
### Some helper functions
###

def starts_conversation(comment):
    """Returns True if this comment starts a conversation"""
    return comment[0] == '0'

###
### Main
###

# Grab total number of lines in all-years.csv from command line
if len(sys.argv) != 3:
    sys.exit("Usage: python3 tenpc.py `wc -l annotations/all-years.csv`")
tot_records = int(sys.argv[1])
num_grabbed = int(tot_records * PERCENT_GRABBED / 100) 

# We grab all the records in the all-years files for both output
# files in the following code because it is easier to deal with 
# the loop bound when we write out the tbcoded file.
with open(FNAME_DATA) as fdata, \
     open(FNAME_KEY) as fkey:
    data_reader = csv.reader(fdata, delimiter=',')
    key_reader = csv.reader(fkey, delimiter=',')

    # Note: record count is 0-based and conversation count is not
    record = 0    # an index into a CSV file
    c = 0         # conversation number (starts at 1)

    # Handle header record
    try:
        # Throw away existing headers
        d_row = next(data_reader)
        k_row = next(key_reader)

        # Create new header
        new_header = ['Conversation', 'Authentic?', 'Rich?', 'Comment']
        new_tbdata.append(new_header)
        new_ardata.append(new_header)
        record += 1

    except StopIteration:
        raise RuntimeError('Unexpected empty CSV file')

    # Prepare to begin translation
    try:
        d_row = next(data_reader)
        k_row = next(key_reader)
        assert(starts_conversation(d_row))
    except StopIteration:
        raise RuntimeError('Nothing but a header in CSV file')

    # Translate
    while True:
        if starts_conversation(d_row):
            c += 1

        new_row = [c, 0, 0, d_row[1]]
        new_tbdata.append(new_row)
        new_row = [c, k_row[5], k_row[6], d_row[1]]
        new_ardata.append(new_row)
        record += 1

        # Try to grab the next record and loop back
        try:
            d_row = next(data_reader)
            k_row = next(key_reader)
        except StopIteration:
            break    # all records have been coded

# Write out the to-be-coded data
with open(FNAME_TBNEW, mode='w') as fout:
    csv_writer = csv.writer(fout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)
    for i, new_row in enumerate(new_tbdata):
        if i > num_grabbed:  # use > to deal with header line
            # We only write out the PERCENT_GRABBED in this file
            break
        csv_writer.writerow(new_row)
print(f'Wrote {FNAME_TBNEW}')

# Write out the already-coded data
with open(FNAME_ARNEW, mode='w') as fout:
    csv_writer = csv.writer(fout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)
    for new_row in new_ardata:
        csv_writer.writerow(new_row)
print(f'Wrote {FNAME_ARNEW}')
