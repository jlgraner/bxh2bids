

import bxh2bids
import os
import json

#The sessions you wish to put into BIDS format right now
to_run = ['YYYYMMDD_#####']

#The json file containing information about your study sessions
hopes_dreams_file = '[[YOUR_PATH_HERE]]/bxh2bids_hopes_dreams.json'


#--------DO NOT EDIT BELOW THIS LINE-------------#
with open(hopes_dreams_file) as fd:
    hopes_dreams = json.loads(fd.read())

source_study_dir = hopes_dreams['source_study_dir']
target_study_dir = hopes_dreams['target_study_dir']
ses_info_dir = hopes_dreams['ses_info_dir']
ses_files = hopes_dreams['ses_files']
log_dir = hopes_dreams['log_dir']

bad_data = []
good_data = []
for unique_id in to_run:
    dataid = unique_id
    ses_info_file = os.path.join(ses_info_dir, hopes_dreams['ses_files'][dataid])
    with open(ses_info_file) as fd:
        ses_dict = json.loads(fd.read())

    try:
        bxh2bids.multi_bxhtobids(dataid, ses_dict, source_study_dir, target_study_dir, log_dir)
        good_data.append(dataid)
    except Exception as ex:
        print('Data set failed to run: '+str(dataid))
        print(ex)
        bad_data.append(dataid)

print('Data that ran: '+str(good_data))
print('Data that did NOT run: '+str(bad_data))