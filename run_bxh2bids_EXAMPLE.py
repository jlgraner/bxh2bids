

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

to_run = [
          'YYYYMMDD_ZZZZZ'
          ]

#Set information about your study sessions
source_study_dir="PATH CONTAINING YOUR 'Data' DIRECTORY"
target_study_dir="WHERE YOU WANT THE BIDS DATA TO BE WRITTEN. THE LAST ELEMENT OF THE PATH WILL BE THE STUDY NAME."
log_dir="DIRECTORY WHERE YOU WANT THIS SCRIPT TO WRITE LOG FILES"
ses_info_dir="DIRECTORY WHERE YOU WILL STORE YOUR SESSION INFO FILES"

#--------DO NOT EDIT BELOW THIS LINE-------------#
bad_data = []
good_data = []
for unique_id in to_run:
    dataid = unique_id
    ses_info_file = os.path.join(ses_info_dir, 'bxh2bids_{}.json'.format(unique_id))
    if not os.path.exists(ses_info_file):
        print('Session info file cannot be found: {}'.format(ses_info_file))
        print('NOTE: As of 10/9/19 bxh2bids requires the session info file names to be of the form: "bxh2bids_YYYYMMDD_ZZZZZ.json".')
        print('Here, YYYYMMDD_ZZZZZ is the scan date and exam number.')
        raise RuntimeError('Session info file not found')
    with open(ses_info_file) as fd:
        ses_dict = json.loads(fd.read())

    try:
        b2b.multi_bxhtobids(dataid, ses_dict, source_study_dir, target_study_dir, log_dir)
        good_data.append(dataid)
    except Exception as ex:
        print('Data set failed to run: '+str(dataid))
        print(ex)
        bad_data.append(dataid)

print('Data that ran: '+str(good_data))
print('Data that did NOT run: '+str(bad_data))
