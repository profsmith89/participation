""" fixup.py: Fix issues with data in `all-years.key.csv`

Given that much of the work done by `build.py` and `code.py` is done a comment
at a time, it was easier to push the clean-up work to this separate script.

I also use this script to fix the errors in the Perusall CSV file.

Author: Mike Smith
Date:   20210905
"""

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
"""

###
### Global variables
###

FNAME_DATA = 'annotations/all-years.csv'
FNAME_KEY = 'annotations/all-years.key.csv'

# Where we collect the updated key data
new_key_data = []

###
### Some helper functions
###

def starts_conversation(comment):
    """Returns True if this comment starts a conversation"""
    return comment[0] == '0'

###
### Main
###

# Fix `Replies` that are incorrect. Sometimes the `Replies` count is incorrect
# because `build.py` deleted one or more instructor comments.  Other times,
# Perusall mistakenly splits conversations, and in such cases, I have to both
# update the `Replies` count at the head of such conversations and sometimes
# zero the `Replies` field in some replies.
with open(FNAME_DATA) as fdata, open(FNAME_KEY) as fkey:
    data_reader = csv.reader(fdata, delimiter=',')
    key_reader = csv.reader(fkey, delimiter=',')

    # Note: record count is 0-based and conversation count is not
    record = 0    # an index into a CSV file
    c = 0         # conversation number (starts at 1)
    replies = 0   # track actual replies in a conversation
    last_start = None

    # Skip over header record
    try:
        d_row = next(data_reader)
        k_row = next(key_reader)
        new_key_data.append(k_row)
        record += 1
    except StopIteration:
        raise RuntimeError('Unexpected empty CSV file')

    # Process the data records
    while True:
        try:
            d_row = next(data_reader)
            k_row = next(key_reader)
            if starts_conversation(d_row):
                if last_start != None and int(last_start[2]) != replies:
                    # Fix recorded replies count in last conversation
                    print(f'Conversation #{c}: replies {last_start[2]} => {replies}')
                    last_start[2] = replies

                # Remember key record of the start of this new conversation
                c += 1
                replies = 0
                last_start = k_row
            else:
                replies += 1
                if k_row[2] != 0:
                    # Perusall bug: no replies should have replies
                    k_row[2] = 0
            new_key_data.append(k_row)
        except StopIteration:
            if last_start != None and int(last_start[2]) != replies:
                # Fix recorded replies count in absolute last conversation
                print(f'Conversation #{c}: replies {last_start[2]} => {replies}')
                last_start[2] = replies
            break

# Write out the updated key data
with open(FNAME_KEY, mode='w') as kout:
    csv_writer = csv.writer(kout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)
    for k_row in new_key_data:
        csv_writer.writerow(k_row)

print(f'Wrote {FNAME_KEY}')