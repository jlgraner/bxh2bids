# Setting up bxh2bids

This assumes you have already downloaded the bxh2bids repository and unzipped it in a directory of your choosing. (Look [here](https://github.com/jlgraner/bxh2bids/blob/Documentation_1/Documentation/01_General_Flow.md) for how to do so.)

### 1) bxh2bids_hopes_dreams.json
Create a new copy of .../bxh2bids/Template_files/bxh2bids_hopes_dreams.json (via `cp` on linux or Copy/Past on Windows or Mac) somewhere outside the git repository. I would recommend putting it in a location that is directly associated with the study you want to use bxh2bids with.

Open the new copy in a text editor.

This file will contain information on where your original data reside and where you would like bxh2bids to write output.
For now we'll deal with the first four fields in the file and revisit the list of "ses_files" later on.
`source_study_dir` should be the directory containing the "Data" directory. bxh2bids expects this directory to have "Anat" and "Func" subdirectories.
