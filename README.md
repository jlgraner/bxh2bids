# bxh2bids

This repository is designed to convert MRI data collected at the Brain Image and Analysis Center [(BIAC)](https://www.biac.duke.edu/) at Duke University into the standard Brain Imaging Data Structure [(BIDS)](http://bids.neuroimaging.io/).

Additional documentation and usage notes are still in progress but can be found in the Documents folder.

## Update Notes:
**05/14/2021**: Added coding of the PhaseEncodeDirection field into sidecare json files for scans acquired with the goal of doing field map correction with opposite-phase-encoded images (also known as the "Blip-up/Blip-down" method). There is now a required "dir" entry in the session info. files for any "fmap" scans. The value for "dir" should be the phase-encode direction of the associated aquisition relative to the participant's head and needs to be set to one of: "AP", "PA", "LR", "RL", "IS", "SI". bxh2bids will then use the information found in the associated nifti file header to determine the i/j/k value to write to the sidecar json. NOTE: FOR NOW, BXH2BIDS WILL ONLY HANDLE fmap FILES WITH THE DESCRIPTIONS "field map" OR "field map reverse". THIS IS TO PREVENT MISHANDLING OF DATA DUE TO UNANTICIPATED ACQUISITION DIFFERENCES. IF YOU HAVE A fmap FILES WITH DIFFERENT DESCRIPTIONS, PLEASE REACH OUT TO JOHN GRANER.

**03/19/2021**: Added check_bxh_descriptions.py to the repository. This script can be called with an input directory (the directory containing your "Data" directory) and a data ID (in the form YYYYMMDD_#####) to check the scan description found in each bxh file against the psd_types.json file. If a description is not found, a GUI will open allowing the user to select the associated BIDS type and BIDS label. This should eliminate needed to manually edit psd_types.json when setting up bxh2bids.

**12/13/2019**: The "...hopes_dreams.json" file is no longer needed at all. The four fields it contained have been moved into the "run_bxh2bids_EXAMPLE.py" file. (So, instead of needed both a "run..." file and a "...hopes_dreams.py" file for each study, you now only need a "run..." file.)

**10/09/2019**: Session info. files must now be named in the form "bxh2bids_YYYYMMDD_ZZZZZ.json", where "YYYYMMDD_ZZZZZ" is the date and exam number. The "...hopes_dreams.json" file no longer requires the "ses_files" field (so you no longer need to add an entry for every scan session!).

## Install Dependencies
run 
```
pip install -r requirements.txt
```
