"""code.py: Helps code a randomized dataset of Perusall annotations

The script allows the coder to stop and restart, but they must always
finish coding a conversation before being given the option to stop.

Author: Mike Smith
Date:   20210902
"""

import sys
import csv
import textwrap

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

# By default, we discard any existing coding in the key file. If
# you set this variable to False, coding will begin wherever we
# left off. Coding always starts from the top of the file down.
overwrite = True

# Where we collect the updated key data
new_key_data = []

###
### Some helper functions
###

def starts_conversation(comment):
    """Returns True if this comment starts a conversation"""
    return comment[0] == '0'

def my_pprint(comment, wrapper):
    """Print a comment using the line wrapper provided"""
    wrapped = wrapper.wrap(comment)
    for line in wrapped:
        print(line)

###
### Main
###

# Grab any options on command line
if len(sys.argv) == 2 and sys.argv[1] == '-keep':
    overwrite = False
elif len(sys.argv) > 2:
    sys.exit("Usage: python3 code.py [-keep]")

# Perform coding
with open(FNAME_DATA) as fdata, \
     open(FNAME_KEY) as fkey:
    data_reader = csv.reader(fdata, delimiter=',')
    key_reader = csv.reader(fkey, delimiter=',')
    wrapper = textwrap.TextWrapper(width=60, initial_indent='  ',
                                subsequent_indent='  ')

    # Note: record count is 0-based and conversation count is not
    record = 0    # an index into a CSV file
    c = 0         # conversation number (starts at 1)

    # Handle header record
    try:
        d_row = next(data_reader)
        k_row = next(key_reader)
        new_key_data.append(k_row)
        record += 1
    except StopIteration:
        raise RuntimeError('Unexpected empty CSV file')

    if not overwrite:
        # Skip forward until we find uncoded records
        while True:
            try:
                d_row = next(data_reader)
                k_row = next(key_reader)
            except StopIteration:
                raise RuntimeError('Dataset is fully coded')

            if k_row[5] == '':
                # Break out of infinite loop so we can code this comment,
                # which should start a conversation.
                assert(starts_conversation(d_row))
                break
            else:
                new_key_data.append(k_row)
                if starts_conversation(d_row):
                    c += 1
                record += 1
    else:
        # Prepare to begin coding
        try:
            d_row = next(data_reader)
            k_row = next(key_reader)
            assert(starts_conversation(d_row))
        except StopIteration:
            raise RuntimeError('Nothing but a header in CSV file')

    # Avoid prompting unnecessarily as we start coding
    last_k_row = None

    # Code remaining comments
    while True:
        if starts_conversation(d_row):
            if last_k_row != None:
                # Grab the `rich` coding for the last conversation
                ans = input('Rich discussion? ')
                last_k_row[6] = ans

            # Stuff we do at the start of a conversation
            c += 1
            last_k_row = k_row
            print('')
        else:
            print('REPLY in ', end='')

        # Prompt user to code this comment
        print(f'Conversation #{c}, comment #{record}:')
        my_pprint(d_row[1], wrapper)

        # Grab the authenticity coding, or quit if at start of a conversation
        if starts_conversation(d_row):
            ans = input('Authentic [type `q` to stop]? ')
            if ans == 'q':
                # Move this and any subsequent key rows
                new_key_data.append(k_row)
                while True:
                    try:
                        k_row = next(key_reader)
                        new_key_data.append(k_row)
                    except StopIteration:
                        break  # out of the inner infinite loop
                break          # out of the outer infinite loop
        else:
            ans = input('Authentic? ')
        k_row[5] = ans
        k_row[6] = 0    # always fill every field

        # Done with coding this comment
        new_key_data.append(k_row)
        record += 1

        # Try to grab the next record and loop back
        try:
            d_row = next(data_reader)
            k_row = next(key_reader)
        except StopIteration:
            # Code and record the quality of the last discussion
            ans = input('Rich discussion? ')
            last_k_row[6] = ans
            print('')
            break    # all records have been coded

# Write out the updated key data
with open(FNAME_KEY, mode='w') as kout:
    csv_writer = csv.writer(kout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)
    for k_row in new_key_data:
        csv_writer.writerow(k_row)

print(f'Wrote {FNAME_KEY}')
