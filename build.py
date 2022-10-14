"""build.py: Builds a randomized database of Perusall annotations.

This script expects two input CSV files on the command line, corresponding to
two different years of Perusall annotations.  It builds and outputs two CSV
files.  The first output file (`all-years.csv`) randomizes the conversations
from the documents that were read in both years.  It also removes the instructor
comments from all conversations; you must hardcode the instructors for each year
into the `instructors` dictionary.  The second output file (`all-years.key.csv`)
maps the conversations in the first output file back to their original years and
keeps the data fields necessary for the statistics we want to calculate.

NOTE: The script expects to find the input files in a subdirectory called
`annotations`.

Author: Mike Smith
Date:   20210901
"""

import sys
import csv
import random
from overlap import overlap

"""Format of the input and output CSV files

--- Fields in original annotation file from Perusall ---
0: Last name, 1: First name, 2: Student ID
3: Submission -- the actual text of the annotation
4: Type -- {comment, question}
5: Score -- [0-2]
6: Created, 7: Last edited at -- date time format
8: Replies, 9: Upvoters
10: Status -- ???
11: Document, 12: Page number
13: Range -- description of annotation anchor {text, rectangle} in document

Note: When I first split the original annotation file by overlap,
I don't change any of the fields.

--- Fields in `all-years` list ---
0: Reply [0 if comment is not; 1 if it is]
1: Our student ID
2: Submission -- the actual text of the annotation
3: Replies
4: Upvoters
5: Document

Note: The list of fields immediately above must be the union of the next
two field lists, not including the any fields filled in during coding.

--- Fields in `all-years` CSV file ---
0: Reply [0 if comment is not; 1 if it is]
1: Submission -- the actual text of the annotation

--- Fields in `all-years.key` CSV file ---
0: Year
1: Our student ID
2: Replies
3: Upvoters
4: Document
5: Authentic? -- coding field
6: Rich discussion? -- coding field
"""

###
### Global variables that specialize this script
###

# Instructor names (last+first without a space) associated with each CSV file.
# We use this list to strip out the instructor comments.
instructors = {
    '1920.csv': ['SmithMichael'],
    '1921.csv': ['SmithMichael'],
    '2020.csv': ['SmithMichael', 'WaldoJim', 'CabralAlex', 'CuiRita',
                 'LeeDianne', 'GandhiVarun'],
    '2021.csv': ['SmithMichael', 'CabralAlex', 'EppsAvriel',
                 'Romero-BrufauSantiago'],
}

# List of fields used in creating all_years
fields = [2, 3, 6, 8, 9, 11, 13]

###
### Global variables
###

# Filenames of the input annotation CSV files
files = []

# Header and records for all-years dataset
header = []
all_years = []

# Keeps track of where each input file starts and ends in all_years
start = {}

# Use a fixed random sequence when testing
testing_seed = None

###
### Some helper functions
###

def no_overlap(docs):
    """Returns True if no overlapping documents were found"""
    for d in docs:
        if docs[d] == 'both':
            return False
    return True

def process_header(row, cur_header):
    """Take the header row, create a header string based on the fields we use in
       this script, and return it.  Along the way, we make sure all input files
       generate the same header.  If they don't, our input CSV files use a
       different layout of fields.
    """
    # Build a stripped-down header line for the current input file
    new_header = []
    for i in fields:
        new_header.append(row[i])

    # Check to make sure this new header looks like the last, if any
    assert(cur_header == [] or cur_header == new_header)
    
    return new_header

def print_conversation(all_years, i):
    """Given a list of comments grouped into conversations and the index of
       the start of a conversation to print, print it.
    """
    print(f'{i}: {all_years[i]}')
    i += 1
    while i < len(all_years) and all_years[i][0] == 1:
        # Print replies in conversation
        print(f'    {i}: {all_years[i]}')
        i += 1

def write_conversation(all_years, i, data_writer, key_writer):
    """Given a list of comments grouped into conversations and the index of the
       start of a conversation to write, write it to both the data and key CSV
       files.  In each file, write just the all-years fields specified in this
       script's opening format comment.
    """
    # Grab the comment and its year
    comment = all_years[i]
    year = find_year(i)

    # Write comment at index i across the two CSV files, plus any coding fields
    # used in coding.py 
    data_writer.writerow([comment[0], comment[2]])
    key_writer.writerow([year, comment[1], comment[3], comment[4], comment[5],
                         '', ''])

    # Write out the replies, if any
    i += 1
    while i < len(all_years) and all_years[i][0] == 1:
        comment = all_years[i]
        data_writer.writerow([comment[0], comment[2]])
        key_writer.writerow([year, comment[1], comment[3], comment[4], comment[5],
                            '', ''])
        i += 1

def find_year(i):
    """Given an index of a comment in all_years, return its filename (i.e.,
       this comment's year, if we named our input files appropriately).
    """
    for fin in start:
        index_start, index_end = start[fin]
        if i >= index_start and i <= index_end:
            return fin.split('.')[0]
    raise ValueError('Index out of range')

def by_conversation(e):
    """Defines the sorting criteria for pulling comments into conversations. The
       element is a record that follows the fields in Perusall's original
       annotation file.  To build conversations, we sort by the following fields
       in priority order: Document, Page number, Range, and Created, which are
       all strings.
    """
    return e[11] + e[12] + e[13] + e[6]

###
### main
###

# Grab the input files -- FIXME: no input validation!
if len(sys.argv) == 1:
    # Prompt user for file and seed information
    print('Enter 1st CSV file: ', end='')
    files.append(input())
    print('Enter 2nd CSV file: ', end='')
    files.append(input())
    print('Enter seed (0 uses current time): ', end='')
    s = int(input())
    testing_seed = s if s > 0 else None
elif len(sys.argv) == 3:
    files.append(sys.argv[1])
    files.append(sys.argv[2])
elif len(sys.argv) == 5:
    files.append(sys.argv[1])
    files.append(sys.argv[2])
    testing_seed = int(sys.argv[4])
else:
    sys.exit('Usage: python3 build.py yr1.csv yr2.csv [-seed N]')

# Figure out what documents the two years have in common
print('--- Computing overlap')
docs = overlap(files)
if no_overlap(docs):
    raise RuntimeError('No overlapping documents in input files')
print('--- Building all-years')

# Split each input csv file into ds-overlap and ds-unique while discarding
# instructor records.
for fname in files:
    # Remember starting location of this input file in all_years
    index_begin = len(all_years)

    # Lists used for splitting one CSV file into the overlapping and
    # non-overlapping documents across all CSV files.
    ds_overlap = []
    ds_unique = []

    # Distribute student records into ds_overlap and ds_unique
    with open(f'annotations/{fname}') as fin:
        csv_reader = csv.reader(fin, delimiter=',')
        line = 0

        for row in csv_reader:
            if line == 0:
                header = process_header(row, header)
            else:
                # Make sure to skip any instructor comments
                if f'{row[0]}{row[1]}' not in instructors[fname]:
                    if docs[row[11]] == 'both':
                        ds_overlap.append(row)
                    else:
                        ds_unique.append(row)
            line += 1

    print(f'Processed {line} lines in {fname}')

    # Pull the comments in a converstion together
    ds_overlap.sort(key=by_conversation)

    # Append ds-overlap to all-years
    all_years += ds_overlap

    # Record beginning and ending location of input file in all_years
    start[fname] = [index_begin, len(all_years)-1]

    # Currently, we do nothing with ds_unique.  It exists at this point in the
    # script in case we decide later to analyze this data.

# Report out the count of comments in all_years
num_comments = len(all_years)
print(f'{num_comments} student annotations in all-years')
print(f'Layout: {start}')

# Strip out unneeded fields from each comment in all_years, compute a unique
# student-id for our own uses, mark those comments that are replies, and
# remember the indices of those comments that begin a conversation, which is the
# list we'll randomize.
prev_range = None
students = {}
next_student_suffix = 0
num_conversations = 0
indices = []
for i, comment in enumerate(all_years):
    # Remember the Range-in-Document before we delete it
    cur_range = comment[13] + comment[11] + comment[12]

    # Compute a unique student-id for our use.  Our student ids are of the form
    # `YYYYssss` where `'YYYY'` is the year the student took the class and
    # `'ssss'` is the 4-digit unique suffix for this student.  This approach
    # assumes that we will never have more than 1000 students combined in any
    # two years.
    year = comment[6].split('-')[0]
    student = comment[0] + comment[1] + year
    student_id = students.get(student)
    if student_id == None:
        student_id = int(year) * 1000 + next_student_suffix
        students[student] = student_id
        next_student_suffix += 1

    # Delete fields not needed in our all-years files
    del comment[12:]
    del comment[10]
    del comment[4:8]
    del comment[0:3]

    # Prepend our `Student ID` field
    comment.insert(0, student_id)

    # Then prepend `Reply` field
    if cur_range == prev_range:
        # Current comment is a reply
        comment.insert(0, 1)
    else:
        # Current comment starts a new conversation
        comment.insert(0, 0)
        num_conversations += 1
        indices.append(i)
    prev_range = cur_range
print(f'{num_conversations} conversations in all-years')

print('Head of CONCATENATED dataset:')
for c in range(3):  # print 3 conversations
    print(f'  {c}/', end='')
    print_conversation(all_years, indices[c])

# Randomize the order of the conversations in all_years by
# randomizing the list of conversation indices.
random.seed(testing_seed)
random.shuffle(indices)

print('Head of RANDOMIZED dataset')
for c in range(3):  # print the first 3 conversations
    print(f'  {c}/', end='')
    print_conversation(all_years, indices[c])

# Create the `all-years` and `all-years.key` CSV files with
# appropriate headers.  Both files use the same randomized order.
with open('annotations/all-years.csv', mode='w') as fout, \
     open('annotations/all-years.key.csv', mode='w') as kout:
    data_writer = csv.writer(fout, delimiter=',', quotechar='"',
                             quoting=csv.QUOTE_MINIMAL)
    key_writer = csv.writer(kout, delimiter=',', quotechar='"',
                            quoting=csv.QUOTE_MINIMAL)

    # Write each file's header
    data_writer.writerow(['Reply', 'Submission'])
    key_writer.writerow(['Year', 'Student ID', 'Replies', 'Upvotes', 'Document',
                         'Authentic?', 'Rich discussion?'])

    for c in range(num_conversations):
        write_conversation(all_years, indices[c], data_writer, key_writer)

print('Wrote annotations/all-years.csv and annotations/all-years.key.csv')
