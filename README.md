The code in this directory helps us to (social science) code and analyze the
Perusall annotations from AC221 in the years 2020 and 2021. The code was used
in "Motivating Data Science Students to Participate and Learn" by Deniz Marti
and Mike Smith, accepted for publication in Harvard Data Science Review.

### Synopsys of usage

```
python3 build.py year1.csv year2.csv [-seed N]
python3 fixup.py
python3 code.py [-keep]
python3 analyze.py year1 year2
python3 tenpc.py

Load gendata.Rmd in RStudio
```

### Usage and description of scripts

These tools assume you want to compare and analyze two different years of
Perusall data.  Let's call them `year1` and `year2`.  The workflow begins with
the downloading of two CSV files: the first corresponds to the Perusall
annotations for year 1 (`year1.csv`) and the second for year 2 (`year2.csv`).
You should put these CSV files in a subdirectory called `annotations`.

The `annotations` directory in this repo contains two example CSV files for
two made-up years.

**Step 1.** Create the `all-years.csv` and `all-years.key.csv` files with the
following command:

```
python3 build.py year1.csv year2.csv
```

This script determines which documents were assigned in both years; you can run
`overlap.py` directly to see the same information.  It then splits each year
into a set of comments corresponding to the documents in the overlap and those
that were unique to that year.  At this time, we do nothing with the comments in
the latter set.

While `build.py` does this initial split, it also removes instructor comments.
Note, however, that it doesn't fix up any `Replies` counts, which we'll do later
in `fixup.py`.

For the comments in the overlap document set, `build.py` next pulls all comments
corresponding to a conversation such that they occur sequentially.  The CSV file
comes sorted by the creation time of each comment, but we want to see the
comments by conversation.

It then puts all conversations on documents in the overlap set from both input
files into a single list and randomly shuffles all these conversations.

Finally, `build.py` writes out the `all-years.csv` and `all-years.key.csv` files
with the fields described in a comment at the top of the script.  The
`all-years.csv` file can be viewed directly by a social science coder as it
doesn't contain any information that may bias the coder. The key file contains
the sensitive information we'll need for analysis.

**Step 2.** Run `fixup.py` to clean up the data in `all-years.key.csv`.  You run the script as follows:

```
python3 fixup.py
```

Currently, the only fixup performed is to fix the `Replies` field on the comment
that starts a conversation in which we originally had one or more instructor
comments.  Recall that we deleted these instructor comments in `build.py`, but
we didn't adjust the `Replies` field (because the instructor comment and the
comment with the effected `Replies` field were some undetermined number of
records apart).

This script also fixes a problem with the way Perusall computes the number of
replies in a conversation.  See comments in the script for details.

**Step 3.** Use `code.py` to annotate the comments and conversations in
`all-years.csv`.  The coding data is stored in `all-years.key.csv`.  You run
the script as follows:

```
python3 code.py [-keep]
```

The script allows the coder to stop and restart the coding where they left off.
It requires the coder to finish coding any conversation they started.  To
restart where you left off, you run the script with the `-keep` flag.  Without
this flag, the script assumes you want to start coding at the top of
`all-years.csv`, overwritting any previous coding work.

**Step 4.** We are now ready to produce statistics of interest using
`analyze.py` as follows:

```
python3 analyze.py year1 year2
```

Although you should finish coding the entire `all-years` file before running
this script, it will run on a partially coded file.  When done in this manner,
it computes statistics for only the part of the dataset that was coded.

**Step 5.** For inter-coder reliability testing, we create two CSV file with 4
fields from the original `all-years` files.  The size of the to-be-coded file
depends on the global variable called `PERCENT_GRABBED`.  It defaults to 10%,
which is the first 10% of the input `all-years` files.

```
python3 tenpc.py `wc -l annotations/all-years.csv`
```

The 4 fields in order are conversation number, authenticity score (0-2),
richness score (0-2), and text of the student comment.  The comments are grouped
by conversation and are in the order of the original conversation.

For the to-be-coded file, we expect that the user will enter the discussion's
richness score on the first comment of the conversation and 0 in the
richness-score field of every reply, if any, which is what `code.py` would have
done and what you'll find in the already-coded output file.

**Step 6.** Although `analyze.py` produces some statistics, the specific
statistics in the paper were generated using `gendata.Rmd` running under
RStudio.