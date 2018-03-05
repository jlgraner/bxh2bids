# Goals of bxh2bids

The goal of this library is to make it as easy as possible to convert data collected at the
Brain Image and Analysis Center [(BIAC)](https://www.biac.duke.edu/) at Duke University into the
standard Brain Imaging Data Structure [(BIDS)](http://bids.neuroimaging.io/). It does this by reading
image information from the .bxh headers and translating this information into the format BIDS requires.

Because there is great variety in the way functional imaging data and associated task-related
behavioral data are collected and saved, the conversion process of BIAC data to BIDS cannot
be fully automated in a single general package. However, this documentation will attempt to guide the user
in the creation of files when necessary.

# General Flow

Current general flow of initial setup and usage:
#### 1. Download the repository from GitHub and save it onto the system from which you'll be running it.
   - If you have git installed, you can use `git clone https://github.com/jlgraner/bxh2bids`  
       OR
   - Navigate to https://github.com/jlgraner/bxh2bids in a web browser and use the "Clone or Download" button.
#### 2. Make sure you have some required python libraries installed
   - The library you are most likely to not have installed already is xmltodict. This should be easily installable
     via pip (`pip install xmltodict`). However, if this doesn't work the package can be downloaded [here](https://pypi.python.org/pypi/xmltodict).
#### 3. Edit/create a couple files so bxh2bids can find your data and match functional .bxh files to specific tasks.
#### 4. Edit run_bxh2bids.py and call it via python in a commmand line.

Once things are set up, running new data sessions just requires a subset of step 3 and then step 4.

See other documentation files for more detailed information.
