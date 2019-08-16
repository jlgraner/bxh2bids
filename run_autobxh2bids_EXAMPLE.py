

import os, sys
import json

#This is clunky, but lets this script get to bxh2bids from anywhere.
this_env = os.environ
#REPLACE THE RIGHT HALF OF THE FOLLOWING LINE TO THE PATH TO YOUR
#COPY OF THE bxh2bids DIRECTORY AS A STRING.
bxh2bids_dir = "[[DIRECTORY CONTAINING YOUR bxh2bids.py FILE]]"

sys.path.append(bxh2bids_dir)
import bxh2bids as b2b

#The sessions you wish to put into BIDS format right now

to_run = {
          'YYYMMDD_ZZZZZ': {'ses':'[[BIDS SES]]', 'sub':'[[SUBJECT ID 1]]'}
          }

source_study_dir = "[[PATH CONTAINING YOUR 'Data' DIRECTORY]]"
target_study_dir = "[[WHERE YOU WANT THE BIDS DATA TO BE WRITTEN. THE LAST ELEMENT OF THE PATH WILL BE THE STUDY NAME.]]"
events_files_dir = "[[DIRECTORY WHERE YOU WILL STORE YOUR SESSION INFO FILES]]"
log_dir = "[[DIRECTORY WHERE YOU WANT THIS SCRIPT TO WRITE LOG FILES]]"


#--------DO NOT EDIT BELOW THIS LINE-------------#
bad_data = []
good_data = []
for unique_id in to_run:
    dataid = unique_id
    data_info = to_run[dataid]

    try:
        b2b.multi_autobxhtobids(dataid, data_info, source_study_dir, target_study_dir, events_files_dir, log_dir)
        good_data.append(dataid)
    except Exception as ex:
        print('Data set failed to run: '+str(dataid))
        print(ex)
        bad_data.append(dataid)

print('Data that ran: '+str(good_data))
print('Data that did NOT run: '+str(bad_data))