# Setting up bxh2bids

This assumes you have already downloaded the bxh2bids repository and unzipped it in a directory of your choosing. (Look [here](https://github.com/jlgraner/bxh2bids/blob/Documentation_1/Documentation/01_General_Flow.md) for how to do so.)

### 1) run_bxh2bids_EXAMPLE.py
Create a new copy of .../bxh2bids/Template_files/run_bxh2bids_EXAMPLE.py (via `cp` on linux or Copy/Past on Windows or Mac) somewhere outside the git repository. I would recommend putting it in a location that is directly associated with the study you want to use bxh2bids with. Rename the copy, replacing "EXAMPLE" with your study name.

Open the new copy in a text editor.

This file is ultimately what you'll call with python to run bxh2bids. It will also contain information on where your original data reside and where you would like bxh2bids to write output.

The first thing you'll need to edit is the line that starts with "bxh2bids_dir". Replace the text between the double-quotes with the path of your local copy of the bxh2bids repository. *EXAMPLE:* If you saved the repository as `/mydir/code/bxh2bids`, then `bxh2bids_dir` should be set to: `/mydir/code/bxh2bids`.

Next, there are four variables you'll have to set involving data input/output locations. (The four lines after "#Set information about your study sessions".)

`source_study_dir` should be the directory containing the "Data" directory. bxh2bids expects this "Data" directory to have "Anat" and "Func" subdirectories. *EXAMPLE:* If my original data are in a directory structure that looks like this: `/mydir/studies/mystudy01/orig/Data/Anat/19000101_12345/scan1.bxh`, then `source_study_dir` should be set to: `/mydir/studies/mystudy01/orig`.

`target_study_dir` is the directory to which you want bxh2bids to write the BIDS-format version of your data. The final piece of the path will be the BIDS study name. *EXAMPLE:* If I want to set my study name to "MyAwesomeStudy" and I want the BIDS version of the data to end up in a new directory in `/mydir/studies/BIDS/` I would set `target_study_dir` to: `/mydir/studies/BIDS/MyAwesomeStudy`.

`log_dir` is a directory to which you want bxh2bids to write log files. This can be anywhere. The log files will be ASCII text files and shouldn't be very big. *EXAMPLE:* I personally tend to keep log files near my data, so I might set this to something like: `/mydir/studies/BIDS/logs`, but its location is at your descretion.

`ses_info_dir` is a directory in which you will store bxh2bids session information files. These files (which we will create in the next section) contain some basic information that tells bxh2bids what type of imaging data are associated with each .bxh file. This dierectory can be anywhere but I would recommend putting it close to your copied `bxh2bids_hopes_dreams.json` file. *EXAMPLE:* If my hopes/dreams file is here: `/mydir/studies/mystudy01/bxh2bids_hopes_dreams.json` I would probably set `ses_info_dir` to: `/mydir/studies/mystudy01/bxh2bids_ses_info`.

### 2) Session Info. Files
If it doesn't exist yet, create the `ses_info_dir` you specified in your copied and edited run_bxh2bids_YOURSTUDY.py file. Then create a new copy of .../bxh2bids/Template_files/bxh2bids_YYYYMMDD_ZZZZZ.json in that session info directory.

The session info files link the secific images in the original Data directory to the categories of images BIDS recognizes. The files also allow you to specify any additional BIDS tag values for each image.
