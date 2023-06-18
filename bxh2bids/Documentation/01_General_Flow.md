# Goals of bxh2bids

The goal of this library is to make it as easy as possible to convert data collected at the
Brain Image and Analysis Center [(BIAC)](https://www.biac.duke.edu/) at Duke University into the
standard Brain Imaging Data Structure [(BIDS)](http://bids.neuroimaging.io/). It does this by reading
image information from the .bxh headers and translating this information into the format BIDS requires.

Because there is great variety in the way functional imaging data and associated task-related
behavioral data are collected and saved, the conversion process of BIAC data to BIDS cannot
be fully automated in a single general package. However, this documentation will attempt to guide the user
in the creation of files when necessary.

# Getting the Code

#### 1. Download the repository from GitHub and save it onto the system from which you'll be running it.
   - If you have git installed, you can use `git clone https://github.com/jlgraner/bxh2bids`  
       OR
   - Navigate to https://github.com/jlgraner/bxh2bids in a web browser and use the "Clone or Download" button.
#### 2. Make sure you have some required python libraries installed
   - The library you are most likely to not have installed already is xmltodict. This should be easily installable
     via pip (`pip install xmltodict`). However, if this doesn't work the package can be downloaded [here](https://pypi.python.org/pypi/xmltodict).

# Run Via Local Install or In-Place
As of v2.0, bxh2bids can be installed via setup.py and called directly from the command line. However, all versions of bxh2bids can be run without local installation by editing the run_bxh2bids_EXAMPLE.py script (see [02_Initial_Setup](bxh2bids/Documentation/02_Initial_Setup.md) for details)
