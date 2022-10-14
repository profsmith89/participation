""" analyze.py: Performs the analyses we use in our paper

Author: Mike Smith
Date:   20211105
"""

import sys
import csv
import re
import string
import statistics

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

# Years found in `all-years.key.csv`.  The order here matters as the script will
# print the results for `years[0]` before `years[1]`.
years = []

###
### Some helper functions
###

def starts_conversation(comment):
    """Returns True if this comment starts a conversation"""
    return comment[0] == '0'

def words_in(s):
    """Returns a count of the words in the string s

    It should surprise no one that the taken approach is not perfect.  In
    general, it removes punctuation marks, which means that any words separated
    by a hypen get run together and counted as one word (e.g., 'out-of-the-box
    testing' becomes the two words 'outofthebox testing').  Words like 'e.g.'
    become 'eg' and missed spaces at the end of a sentence or after a comma
    mistakenly run words together.  But it is good enough for our purposes,
    since the same thing is done to each year.
    """
    words = re.sub('['+string.punctuation+']', '', s).split()
    return len(words)

###
### Main
###

# Grab the years in the analysis
if len(sys.argv) == 1:
    print('Enter 1st year: ', end='')
    years.append(input())
    print('Enter 2nd year: ', end='')
    years.append(input())
elif len(sys.argv) == 3:
    years.append(sys.argv[1])
    years.append(sys.argv[2])
else:
    sys.exit('Usage: python3 analyze.py year1 year2')


with open(FNAME_DATA) as fdata, open(FNAME_KEY) as fkey:
    data_reader = csv.reader(fdata, delimiter=',')
    key_reader = csv.reader(fkey, delimiter=',')

    # Some simple counts from each year
    record = 0             # an index into the CSV files
    num_comments = [0, 0]
    num_conversations = [0, 0]
    num_upvotes = [0, 0]

    # The list m is where we gather that data from which we derive our more
    # detailed metrics.  Each year in m is a list of 6 lists.  Each of the 6
    # lists pulls together the data on one characteristic of the conversations
    # in that year.  For example, the first of the 6 lists is an array
    # containing the number of comments found in each of that year's
    # conversations.  We generate a constant describing which of the 6 lists
    # collects what.
    m = [[[],[],[],[],[],[]], [[],[],[],[],[],[]]]
    C_COMMENTS = 0
    C_STUDENTS = 1
    C_UPVOTES = 2
    C_WORDS = 3
    C_AUTHENTIC = 4
    C_RICH = 5
    C_END = 6        # marks end of list of conversation characteristics

    # Let's get to it.  We start by skipping over the header record.
    try:
        d_row = next(data_reader)
        k_row = next(key_reader)
        record += 1
    except StopIteration:
        raise RuntimeError('Unexpected empty CSV file')

    # This is where we keep the characteristics of interest of the currently
    # processed conversation.  It is indexed by the same `C_*` constants.
    cur_cc = None

    # The set we use to keep track of the number of unique students in the
    # current conversation.
    students = set()

    # Process the data records
    while True:
        try:
            # Read the next record
            d_row = next(data_reader)
            k_row = next(key_reader)

            # Check for incompletely coded input, and if found, breakout after
            # the last coded comment.
            if k_row[5] == '':
                raise StopIteration()

            if starts_conversation(d_row):
                # Finish processing the last conversation, using the last y
                if cur_cc != None:
                    cur_cc[C_STUDENTS] = len(students)
                    for i, x in enumerate(cur_cc):
                        m[y][i].append(x)

                # Clear the students set for this new conversation
                students.clear()

                # Initialize cur_cc with the values in this first comment in the
                # new conversation.
                cur_cc = [1, 1, int(k_row[3]), words_in(d_row[1]),
                          int(k_row[5]), int(k_row[6])]

                # Add the student who made this comment to our students set
                students.add(int(k_row[1]))

            else:
                # Update the set of students and the current conversation's
                # characteristics with this reply's data.
                cur_cc[C_COMMENTS] += 1
                students.add(int(k_row[1]))
                cur_cc[C_UPVOTES] += int(k_row[3])
                cur_cc[C_WORDS] += words_in(d_row[1])
                cur_cc[C_AUTHENTIC] += int(k_row[5])
                cur_cc[C_RICH] += int(k_row[6])

            # Determine the year index for this new record
            record += 1
            if k_row[0] == years[0]:
                y = 0
            elif k_row[0] == years[1]:
                y = 1
            else:
                sys.exit('Unexpected year in input processing')

            # Update a global counts
            num_comments[y] += 1
            num_upvotes[y] += int(k_row[3])
            if starts_conversation(d_row):
                num_conversations[y] += 1

        except StopIteration:
            if cur_cc != None:
                # Finish processing the last conversation, using the last y
                cur_cc[C_STUDENTS] = len(students)
                for i, x in enumerate(cur_cc):
                    m[y][i].append(x)
            else:
                # Nothing coded and so we exit
                sys.exit('Uncoded input')
            break

print(f'Processed {record - 1} data records\n')

# Print the results
for i, yr in enumerate(years):
    print(f'*** {yr} ***')
    print(f'  total comments = {num_comments[i]}')
    print(f'  total conversations = {num_conversations[i]}')
    print('')

    if num_comments[i] == 0:
        continue

    print('  ** QUANTitative measures\n')

    avg = statistics.mean(m[i][C_COMMENTS])
    print(f'  average comments/conversation = {avg}')
    if len(m[i][C_COMMENTS]) > 1:
        sd = statistics.stdev(m[i][C_COMMENTS], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

    avg = statistics.mean(m[i][C_STUDENTS])
    print(f'  average students/conversation = {avg}')
    if len(m[i][C_STUDENTS]) > 1:
        sd = statistics.stdev(m[i][C_STUDENTS], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

    avg = statistics.mean(m[i][C_UPVOTES])
    print(f'  average upvotes/conversation = {avg}')
    if len(m[i][C_UPVOTES]) > 1:
        sd = statistics.stdev(m[i][C_UPVOTES], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

    print('  ** QUALitative measures\n')

    avg = statistics.mean(m[i][C_AUTHENTIC])
    print(f'  average authenticity score/conversation = {avg}')
    if len(m[i][C_AUTHENTIC]) > 1:
        sd = statistics.stdev(m[i][C_AUTHENTIC], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

    avg = statistics.mean(m[i][C_RICH])
    print(f'  average richness score/conversation = {avg}')
    if len(m[i][C_RICH]) > 1:
        sd = statistics.stdev(m[i][C_RICH], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

    print('  ** Fun measures\n')

    avg = statistics.mean(m[i][C_WORDS])
    print(f'  average words/conversation = {avg}')
    if len(m[i][C_WORDS]) > 1:
        sd = statistics.stdev(m[i][C_WORDS], avg)
        print(f'  stdev of the sample = {sd}')
        print('')

# Write out the discussion data for each year
for i, yr in enumerate(years):
    fname = 'annotations/' + yr + '-conversations.csv'
    with open(fname, mode='w') as fout:
        csv_writer = csv.writer(fout, delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)

        # Write out header row
        csv_writer.writerow(['Comments', 'Students', 'Upvotes', 'Words',
                             'Authenticity score', 'Richness score'])

        # Write out data rows
        for j in range(num_conversations[i]):
            # Create the row then write it for conversation i
            c_row = []
            for k in range(C_END):
                c_row.append(m[i][k][j])
            csv_writer.writerow(c_row)

    print(f'Wrote {fname}')