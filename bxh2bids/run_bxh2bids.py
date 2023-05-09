

import os, sys
import json
import bxh2bids.bxh2bids as b2b

def bidsify(proj_dir, biac_dirs):

    #Set information about your study sessions
    source_study_dir=os.path.join(proj_dir, 'sourcedata')
    target_study_dir=os.path.join(proj_dir,'rawdata')
    log_dir=os.path.join(proj_dir,'derivatives','bxh2bids_logs')
    ses_info_dir=os.path.join(proj_dir,'code','bxh2bids_ses_info')

    bad_data = []
    good_data = []
    for unique_id in biac_dirs:
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
