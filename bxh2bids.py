###############################################
#Function:  bxh2bids.py
#
#Purpose:  This script creates a copy of imaging data for use in
#           the BIDS format.  The data are assumed to be stored in the following
#           directory structure:
#               .../STUDY/Data/Anat/ID1
#                                  /ID2
#                             /Func/ID1
#                                  /ID2
#           This script will attempt to create directories associated with an input
#           subject and session number.
#
#           Information on BIDS: http://bids.neuroimaging.io/
#           
#           Right now this script also depends on the file "description_types.json"
#           being in the same directory as this file. "description_types.json" serves
#           as a link between scan descriptions and BIDS modality types.
#
#Inputs:
#           Data ID (original directory number; "IDZ" above) (dataid)
#           Subject BIDS ID/number
#           Session BIDS ID/name
#           Source study dir ("STUDY" above) (source_study_dir)
#           BIDS study dir (contains "sub-zz" directories) (target_study_dir)
#           Log file dir (log_dir)
#
#Outputs:
#          A log file will be written to the passed log directory
#
#Returns:
#          NA
#
#Example Call:
#           
#
#
# Created 09/2017 by John Graner; Center for Cognitive Neuroscience, LaBar Lab, Duke University
############################################

import json
import xmltodict
import os, re, shutil, sys
import logging, time
import bxh_pick_fields
import string
import gzip


def copy_image(image_to_copy, full_output):

    logging.info('--STARTING: copy_image--')

    #If the image to be copied is compressed (e.g. a ".gz")
    #unzip the archive, rename the resulting file, and then
    #create a new archive. This is done to make sure the
    #original file name is not maintained.

    #Read in the input file contents
    logging.info('Reading file to copy: {}'.format(image_to_copy))
    if image_to_copy[-3:] == '.gz':
        with gzip.open(image_to_copy, 'rb') as fi:
            input_contents = fi.read()
    else:
        with open(image_to_copy, 'rb') as fi:
            input_contents = fi.read()

    #Write the contents to the output destination
    logging.info('Writing file: {}'.format(full_output))
    if full_output[-3:] == '.gz':
        with gzip.open(full_output, 'wb') as fo:
            fo.write(input_contents)
    else:
        with open(full_output, 'wb') as fo:
            fo.write(input_contents)

    logging.info('--FINISHED: copy_image--')


def create_dataset_description(target_study_dir, study_name=None):
    
    logging.info('--STARTING: create_dataset_description--')

    #This file always has the same name
    full_output = os.path.join(target_study_dir, 'dataset_description.json')

    #Make sure passed study directory exists
    if not os.path.exists(target_study_dir):
        logging.error('Passed study directory does not exist: '+str(target_study_dir))
        raise RuntimeError('Passed study dir not found.')

    #Check to see if a study name was passed. Otherwise, use the study dir
    if study_name is None:
        study_name = os.path.split(target_study_dir)[-1]
        if study_name == '': #(The path was passed ending with a '/')
            study_name = os.path.split(os.path.split(target_study_dir)[0])[-1]

    #If it doesn't exist, write it.
    if not os.path.exists(full_output):
        output_dict = {'BIDSVersion': '1.0.2',
                       'Name': str(study_name)
                       }
        logging.info('Writing dataset json: '+str(full_output))
        output = json.dumps(output_dict, indent=4)
        with open(full_output, 'w') as fd:
            fd.write(output)
    else:
        logging.warning('Dataset description file already exists!')

    logging.info('--FINISHED: create_dataset_description--')


def match_func(image_to_copy, ses_dict):

    logging.info('--START: match_func--')

    #Isolate the file name
    file_name = os.path.split(image_to_copy)[-1]

    #Start the output name
    output_prefix = 'sub-'+str(ses_dict['sub'])+'_ses-'+str(ses_dict['ses'])

    #Extract information from the session dictionary
    func_scan_strings = ses_dict['funcs'].keys()
    #Try to match the file name with one of the func strings (e.g. '005_01')
    file_identified = 0
    for element in func_scan_strings:
        if element in file_name:
            file_identified = file_identified + 1 #this should never be > 1
            if file_identified > 1:
                logging.error('Func file matched with more than one id string!')
                logging.error('Check your hopes and dreams file!')
                logging.error('File name: '+str(image_to_copy))
                raise RuntimeError('Functional file matched with > 1 id string!')
            taskid = ses_dict['funcs'][element]['task']
            runid = ses_dict['funcs'][element]['run']
            func_id_string = element
    if not file_identified:
        logging.error('Func file not matched with id string!')
        logging.error('Check the session info file to make sure there is a "funcs" entry with this id string.')
        logging.error('File name: '+str(image_to_copy))
        raise RuntimeError('Functional file cannot be matched with id string!')

    logging.info('--FINISHED: match_func--')

    return func_id_string


def match_anat(image_to_copy, ses_dict):

    logging.info('--START: match_anat--')

    #Isolate the file name
    file_name = os.path.split(image_to_copy)[-1]

    #Start the output name
    output_prefix = 'sub-'+str(ses_dict['sub'])+'_ses-'+str(ses_dict['ses'])

    #Extract information from the session dictionary
    if 'anats' in ses_dict.keys():
        anat_scan_strings = ses_dict['anats'].keys()
        #Try to match the file name with one of the func strings (e.g. '005')
        file_identified = 0
        for element in anat_scan_strings:
            if element in file_name:
                file_identified = file_identified + 1 #this should never be > 1
                if file_identified > 1:
                    logging.error('Anat file matched with more than one id string!')
                    logging.error('Check your hopes and dreams file!')
                    logging.error('File name: '+str(image_to_copy))
                    logging.error('BIDS ID: '+str(bidsid))
                    logging.error('Sess ID: '+str(sesid))
                    raise RuntimeError('Anatomical file matched with > 1 id string!')
                else:
                    logging.info('Anat file matched with id string: '+str(element))
                anat_id_string = element
        if not file_identified:
            logging.warning('Anat file not matchted with id string!')
            logging.warning('This may be okay...')
            anat_id_string = None
    else:
        anat_id_string = None

    logging.info('--FINISHED: match_anat--')

    return anat_id_string


def match_fmap(image_to_copy, ses_dict):

    logging.info('--START: match_fmap--')

    #Isolate the file name
    file_name = os.path.split(image_to_copy)[-1]

    #Start the output name
    output_prefix = 'sub-'+str(ses_dict['sub'])+'_ses-'+str(ses_dict['ses'])

    #Extract information from the session dictionary
    if 'fmaps' in ses_dict.keys():
        fmap_scan_strings = ses_dict['fmaps'].keys()
        #Try to match the file name with one of the fmap strings (e.g. '005')
        file_identified = 0
        for element in fmap_scan_strings:
            if element in file_name:
                file_identified = file_identified + 1 #this should never be > 1
                if file_identified > 1:
                    logging.error('fmap file matched with more than one acquisition id string!')
                    logging.error('Check your session info file!')
                    logging.error('File name: '+str(image_to_copy))
                    logging.error('BIDS ID: '+str(bidsid))
                    logging.error('Sess ID: '+str(sesid))
                    raise RuntimeError('Fmap file matched with > 1 acquisition id string!')
                else:
                    logging.info('fmap file matched with acquisition id string: '+str(element))
                fmap_id_string = element
        if not file_identified:
            logging.warning('Fmap file not matchted with acquisition id string!')
            logging.warning('This may be okay...')
            fmap_id_string = None
    else:
        fmap_id_string = None

    logging.info('--FINISHED: match_fmap--')

    return fmap_id_string


def match_dwi(image_to_copy, ses_dict):

    logging.info('--START: match_dwi--')

    #Isolate the file name
    file_name = os.path.split(image_to_copy)[-1]

    #Start the output name
    output_prefix = 'sub-'+str(ses_dict['sub'])+'_ses-'+str(ses_dict['ses'])

    #Extract information from the session dictionary
    if 'dwis' in ses_dict.keys():
        dwi_scan_strings = ses_dict['dwis'].keys()
        #Try to match the file name with one of the dwi strings (e.g. '005')
        file_identified = 0
        for element in dwi_scan_strings:
            if element in file_name:
                file_identified = file_identified + 1 #this should never be > 1
                if file_identified > 1:
                    logging.error('dwi file matched with more than one acquisition id string!')
                    logging.error('Check your session info file!')
                    logging.error('File name: '+str(image_to_copy))
                    logging.error('BIDS ID: '+str(bidsid))
                    logging.error('Sess ID: '+str(sesid))
                    raise RuntimeError('DWI file matched with > 1 acquisition id string!')
                else:
                    logging.info('dwi file matched with acquisition id string: '+str(element))
                dwi_id_string = element
        if not file_identified:
            logging.warning('DWI file not matchted with acquisition id string!')
            logging.warning('This may be okay...')
            dwi_id_string = None
    else:
        dwi_id_string = None

    logging.info('--FINISHED: match_dwi--')

    return dwi_id_string


def create_bold_json(bxh_file, full_output):

    logging.info('---START: create_bold_json---')

    with open(bxh_file) as fd:
        bxh_contents = xmltodict.parse(fd.read())

    #Pull the task name out of the output file name
    taskname = os.path.split(full_output)[-1].split('task-')[-1].split('_')[0]

    ##TODO: Clean this up! Probably move all these to a template file.

    #Calculate total readout time

    #Look for the TR
    try:
        tr = float(bxh_contents['bxh']['acquisitiondata']['tr'])
    except:
        logging.error('TR could not be found in passed .bxh!')
        logging.error('bxh_file: '+str(bxh_file))
        raise RuntimeError('TR could not be found in .bxh.')

    #Put together dictionary of things to write to the sidecar .json file
    #Make sure the func field template file is where it should be
    here = os.path.dirname(os.path.realpath(__file__))
    func_field_file = os.path.join(here, 'info_field_files', 'func_info_fields.json')
    if not os.path.exists(func_field_file):
        logging.error('Functional image sidecar template file cannot be found!')
        logging.error('It should be here: '+str(func_field_file))
        raise RuntimeError('Missing functional sidecar template file!')

    out_dict = bxh_pick_fields.bxh_pick(func_field_file, bxh_as_dict=bxh_contents)

    #Make sure the tr is in seconds
    tr = out_dict['RepetitionTime']
    if tr > 50:
        logging.info('TR in bxh file is greater than 50, assuming it is in ms.')
        tr = tr/1000
        out_dict['RepetitionTime'] = tr

    #Make sure echo time is in seconds
    et = out_dict['EchoTime']
    if et > 1:
        logging.info('Echo Time is greater than 1, assuming it is in ms.')
        et = et/1000
        out_dict['EchoTime'] = et

    #Calculate slice timing
    for element in bxh_contents['bxh']['datarec']['dimension']:
        if element['@type'] == 'z':
            if 'datapoints' in element.keys():
                logging.info('bxh file contains slice order list')
                slice_order_list = element['datapoints']['#text'].split(' ')
                num_slices = float(element['size'])
            else:
                logging.warn('Cannot find slice order in bxh file!')
                logging.warn('Assuming it is interleaved up!')
                num_slices = int(element['size'])
                interleave_order = list(range(1, num_slices+1, 2)) + list(range(2, num_slices+1, 2))
                slice_order_list = [x for _,x in sorted(zip(interleave_order, range(1,num_slices+1)))]
    factor = tr/num_slices
    st = []
    for s in slice_order_list:
        st.append(factor * (int(s)-1))

    out_dict['TaskName'] = taskname
    out_dict['SliceTiming'] = st

    out_string = json.dumps(out_dict, indent=4)

    logging.info('Writing sidecar func file: '+str(full_output))
    with open(full_output, 'w') as out_file:
        out_file.write(out_string)

    logging.info('---FINISHED: create_bold_json---')


def create_anat_json(bxh_file, full_output):

    logging.info('---START: create_anat_json---')

    with open(bxh_file) as fd:
        bxh_contents = xmltodict.parse(fd.read())

    #Put together dictionary of things to write to the sidecar .json file
    #Make sure the anat field template file is where it should be
    here = os.path.dirname(os.path.realpath(__file__))
    anat_field_file = os.path.join(here, 'info_field_files', 'anat_info_fields.json')
    if not os.path.exists(anat_field_file):
        logging.error('Anatomical image sidecar template file cannot be found!')
        logging.error('It should be here: '+str(anat_field_file))
        raise RuntimeError('Missing anatomical sidecar template file!')

    out_dict = bxh_pick_fields.bxh_pick(anat_field_file, bxh_as_dict=bxh_contents)

    #Make sure echo time is in seconds
    et = out_dict['EchoTime']
    if et > 1:
        logging.info('Echo Time is greater than 1, assuming it is in ms.')
        et = et/1000
        out_dict['EchoTime'] = et

    out_string = json.dumps(out_dict, indent=4)

    logging.info('Writing sidecar anat file: '+str(full_output))
    with open(full_output, 'w') as out_file:
        out_file.write(out_string)

    logging.info('---FINISHED: create_anat_json---')


def create_dwi_json(bxh_file, full_output):

    logging.info('---START: create_dwi_json---')

    with open(bxh_file) as fd:
        bxh_contents = xmltodict.parse(fd.read())

    #Pull the task name out of the output file name
    taskname = os.path.split(full_output)[-1].split('task-')[-1].split('_')[0]

    ##TODO: Clean this up! Probably move all these to a template file.

    #Calculate total readout time

    #Put together dictionary of things to write to the sidecar .json file
    #Make sure the func field template file is where it should be
    here = os.path.dirname(os.path.realpath(__file__))
    dwi_field_file = os.path.join(here, 'info_field_files', 'dwi_info_fields.json')
    if not os.path.exists(dwi_field_file):
        logging.error('DWI image sidecar template file cannot be found!')
        logging.error('It should be here: '+str(dwi_field_file))
        raise RuntimeError('Missing functional sidecar template file!')

    out_dict = bxh_pick_fields.bxh_pick(dwi_field_file, bxh_as_dict=bxh_contents)

    #If this is a DTI fmap, there may be an IntendedFor image
    ##TODO: expose the bxh_info_dict to this function so it can handle
    ##the IntededFor field information!!!

    #Make sure the tr is in seconds
    tr = out_dict['RepetitionTime']
    if tr > 50:
        logging.info('TR in bxh file is greater than 50, assuming it is in ms.')
        tr = tr/1000
        out_dict['RepetitionTime'] = tr

    #Make sure echo time is in seconds
    et = out_dict['EchoTime']
    if et > 1:
        logging.info('Echo Time is greater than 1, assuming it is in ms.')
        et = et/1000
        out_dict['EchoTime'] = et

    out_string = json.dumps(out_dict, indent=4)

    logging.info('Writing sidecar func file: '+str(full_output))
    with open(full_output, 'w') as out_file:
        out_file.write(out_string)

    logging.info('---FINISHED: create_dwi_json---')


def create_ncanda_json(bxh_file, full_output):

    logging.info('---START: create_ncanda_fmap_json---')

    with open(bxh_file) as fd:
        bxh_contents = xmltodict.parse(fd.read())

    #Put together dictionary of things to write to the sidecar .json file
    #Make sure the fmap field template file is where it should be
    here = os.path.dirname(os.path.realpath(__file__))
    fmap_field_file = os.path.join(here, 'info_field_files', 'fmap_info_fields.json')
    if not os.path.exists(fmap_field_file):
        logging.error('Fmap image sidecar template file cannot be found!')
        logging.error('It should be here: '+str(fmap_field_file))
        raise RuntimeError('Missing fmap sidecar template file!')

    out_dict = bxh_pick_fields.bxh_pick(fmap_field_file, bxh_as_dict=bxh_contents)

    #Pull apart the two echo times and make sure they are in seconds
    et = out_dict['EchoTime']
    if not (len(et.split(' ')) > 1):
        logging.error('Only one TE found in .bxh header for ncanda fmap!')
        logging.error('There should be exactly two!')
        logging.error('Header entry as read by .bxh_pick: '+str(et))
        logging.error('.bxh file: '+str(bxh_file))
        raise RuntimeError('One TE found in ncanda .bxh header!')

    et_one = float(et.split(' ')[0])
    et_two = float(et.split(' ')[1])

    if et_one > 1:
        logging.info('Echo Time is greater than 1, assuming it is in ms.')
        et_one = et_one/1000
        out_dict['EchoTime1'] = et_one

    if et_two > 1:
        logging.info('Echo Time is greater than 1, assuming it is in ms.')
        et_two = et_two/1000
        out_dict['EchoTime2'] = et_two

    #Remove the old EchoTime dictionary entry, quietly
    out_dict['EchoTime'] = None
    out_dict.pop('EchoTime')

    out_string = json.dumps(out_dict, indent=4)

    logging.info('Writing sidecar fmap file: '+str(full_output))
    with open(full_output, 'w') as out_file:
        out_file.write(out_string)

    logging.info('---FINISHED: create_ncanda_fmap_json---')


def create_bvecs_bvals(bxh_file, bxh_info_dict, output_dir):
    # open DWI bxh file, read b-vector and b-value information 
    # and write into BIDS formatted .bvec and .bval files
    #
    # John Powers, LaBar Lab, Duke University, Nov. 2017
    
    logging.info('---START: create_bvecs_bvals---')
    
    # read in the bxh_file using xmltodict
    logging.info('')
    with open(bxh_file) as dwi_bxh:
        bxh_contents = xmltodict.parse(dwi_bxh.read())

    # generate .bval file name
    bvals_output_name = bxh_info_dict['output_prefix']+'_dwi.bval'
    bvals_full_output = os.path.join(output_dir, bvals_output_name)

    # create .bval file and write in row of b-values from bxh
    with open(bvals_full_output, "w") as bvals:
        bval_line = bxh_contents['bxh']['datarec']['dimension'][3]['datapoints'][1]['#text']
        bvals.write(bval_line)
    
    # initialize strings for b-vector x, y, and z components that will be filled in the for loop
    bvec_x_line = ""
    bvec_y_line = ""
    bvec_z_line = ""

    # create strings of b-vector x, y, and z components
    for element in bxh_contents['bxh']['datarec']['dimension'][3]['datapoints'][0]['value']:
        bvec_x = element.split(" ")[0]
        bvec_y = element.split(" ")[1]
        bvec_z = element.split(" ")[2]
        bvec_x_line += bvec_x + " "
        bvec_y_line += bvec_y + " "
        bvec_z_line += bvec_z + " "
    
    # remove extra space character from the end of these strings
    bvec_x_line = bvec_x_line.strip()
    bvec_y_line = bvec_y_line.strip()
    bvec_z_line = bvec_z_line.strip()

    bvecs_output_name = bxh_info_dict['output_prefix']+'_dwi.bvec'
    bvecs_full_output = os.path.join(output_dir, bvecs_output_name)
    
    # create .bvec file and write x, y, and z components as separate rows
    with open(bvecs_full_output, "w") as bvecs:
        bvecs.write(bvec_x_line + "\n")
        bvecs.write(bvec_y_line + "\n")
        bvecs.write(bvec_z_line)

    logging.info('---FINISH: create_bvecs_bvals---')


output_dir_func = lambda target_study_dir, bxh_info_dict, scan_type: \
    os.path.join(target_study_dir, 'sub-'+bxh_info_dict['sub'], 'ses-'+bxh_info_dict['ses'], scan_type) if bxh_info_dict['ses'] != "" \
    else os.path.join(target_study_dir, 'sub-'+bxh_info_dict['sub'], scan_type) 


def convert_bxh(bxh_file, bxh_info_dict, target_study_dir=None):
    #Read in the bxh_file using xmltodict
    #Pull out:
    #   image file name (doc['bxh']['datarec']['filename']
    #   psdinternalname (for matching with BIDS modality label)
    #   other things later in the script depending on the modality type
    
    logging.info('----START: convert_bxh----')
    
    #Make sure bxh_file is there
    if not os.path.exists(bxh_file):
        raise RuntimeError('Passed file cannot be found: '+str(bxh_file))
    
    #Directory of the bxh file
    bxh_dir = os.path.split(bxh_info_dict['orig_image'])[0]

    if bxh_info_dict['scan_type'] == 'func':

        #Put together the output directory
        output_dir = output_dir_func(target_study_dir, bxh_info_dict, "func")

        if not os.path.exists(output_dir):
            logging.info('Creating directory: '+str(output_dir))
            os.makedirs(output_dir)

        #Copy and rename the functional data
        logging.info('Running copy_func on this .bxh.')

        #Copy the image data
        image_to_copy = bxh_info_dict['orig_image']
        output_name = bxh_info_dict['output_name']
        full_output = os.path.join(output_dir, output_name)
        logging.info('Copying file: '+str(image_to_copy))
        logging.info('Target location: '+str(full_output))
        copy_image(image_to_copy, full_output)

        #Copy a .tsv file if it exists
        if 'tsv_file' in bxh_info_dict.keys():
            #Put together the output prefix
            if bxh_info_dict['output_name'][-3:] == '.gz':
                image_ext = '.nii.gz'
            else:
                image_ext = '.nii'
            if not os.path.exists(bxh_info_dict['tsv_file']):
                raise RuntimeError('tsv_file cannot be found: '+str(bxh_info_dict['tsv_file']))
            tsv_output_name = bxh_info_dict['output_prefix']+'_events.tsv'
            tsv_full_output = os.path.join(output_dir, tsv_output_name)
            #Check to see if the output exists already
            if os.path.exists(tsv_full_output):
                raise RuntimeError('Output file already exists: '+str(tsv_full_output))
            tsv_to_copy = bxh_info_dict['tsv_file']
            logging.info('Copying file: '+str(tsv_to_copy))
            logging.info('Target location: '+str(tsv_full_output))
            shutil.copy2(tsv_to_copy, tsv_full_output)

        output_name = bxh_info_dict['output_prefix']+'_'+bxh_info_dict['scan_label']+'.json'
        full_output = os.path.join(output_dir, output_name)
        create_bold_json(bxh_file, full_output)

    elif bxh_info_dict['scan_type'] == 'fmap':

        #Put together the output directory
        output_dir = output_dir_func(target_study_dir, bxh_info_dict, "fmap")

        #If the output directory does not exist, create it and
        #all upper directories.
        if not os.path.exists(output_dir):
            logging.info('Creating directory: '+str(output_dir))
            os.makedirs(output_dir)

        bxh_desc = bxh_info_dict['bxh_desc']

        #Make sure the data are in a known format
        if bxh_desc == 'ncanda-grefieldmap-v1':
            #There should be three .nii.gz files associated with this acquisition.
            #They should have names in this format, and contain the following:
            #   bia?_?????_0NN_1-1.ni.gz - Magnitude image at two TEs
            #   bia?_?????_0NN_2-2.nii.gz - Real image at two TEs
            #   bia?_?????_0NN_3-3.nii.gz - Imaginary image at two TEs

            #Get the number of this particular image file
            # image_name = bxh_dict['bxh']['datarec']['filename']
            image_name = bxh_info_dict['orig_image']
            fmap_part = image_name.split('.nii')[0][-1]
            if fmap_part == '1':
                b_label = 'magnitude'
            elif fmap_part == '2':
                b_label = 'real'
            elif fmap_part == '3':
                b_label = 'imaginary'
            else:
                logging.error('Could not identify fieldmap number label in file name.')
                logging.error('File name: '+str(image_name))
                logging.error('Number extracted: '+str(fmap_part))
                raise RuntimeError

            #Copy and rename the fmap file
            logging.info('Running copy_ncanda_fmap on this .bxh.')

            if bxh_info_dict['orig_image'][-3:] == '.gz':
                file_type = '.nii.gz'
            else:
                file_type = '.nii'

            #Copy the fmap file
            image_to_copy = bxh_info_dict['orig_image']
            full_output = bxh_info_dict['output_prefix']+b_label+file_type
            #Check to see if the output file already exists
            if os.path.exists(full_output):
                raise RuntimeError('Output file already exists: '+str(full_output))

            #Copy the image data
            logging.info('Copying file: '+str(image_to_copy))
            logging.info('Target location: '+str(full_output))
            copy_image(image_to_copy, full_output)

            #Put together the sidecar .json file
            output_name = bxh_info_dict['output_prefix']+'_'+bxh_info_dict['scan_label']+'.json'
            full_output = os.path.join(output_dir, output_name)
            create_ncanda_json(bxh_file, full_output)

        # elif bxh_desc == 'HCP DTI reverse polarity':
        #     #Data in the same 3D shape as a DTI acquisition, but with only a few volumes
        #     #and with a reversed phase-encode direction.
        #     #The first volume should be a b-value=0 image that can be used for distortion
        #     #correction.

        #     logging.info('Processing reverse polarity DTI data...')

        #     #Copy the fmap file
        #     image_to_copy = bxh_info_dict['orig_image']
        #     output_name = bxh_info_dict['output_name']
        #     full_output = os.path.join(output_dir, output_name)
        #     #Check to see if the output file already exists
        #     if os.path.exists(full_output):
        #         raise RuntimeError('Output file already exists: '+str(full_output))

        #     #Copy the image data
        #     logging.info('Copying file: '+str(image_to_copy))
        #     logging.info('Target location: '+str(full_output))
        #     copy_image(image_to_copy, full_output)

        #     #Put together the sidecar .json file
        #     output_name = bxh_info_dict['output_prefix']+'_'+bxh_info_dict['scan_label']+'.json'
        #     full_output = os.path.join(output_dir, output_name)
        #     create_dwi_json(bxh_file, full_output)

        #     #Create bvec and bval files
        #     logging.info('Creating bvec and bval files for DTI fmap...')
        #     create_bvecs_bvals(bxh_file, bxh_info_dict, output_dir)

        else:
            logging.error('B0 fieldmap description not recognized: '+str(bxh_desc))
            logging.error('These vary too much to make assumptions about how to deal with them.')
            raise RuntimeError

    elif bxh_info_dict['scan_type'] == 'anat':

        #Put together the output directory
        output_dir = output_dir_func(target_study_dir, bxh_info_dict, "anat")

        #If the output directory does not exist, create it and
        #all upper directories.
        if not os.path.exists(output_dir):
            logging.info('Creating directory: '+str(output_dir))
            os.makedirs(output_dir)

        #Copy and rename the anatomical data
        logging.info('Processing anat data...')

        #Prepare to copy the anatomy image data
        image_to_copy = bxh_info_dict['orig_image']
        output_name = bxh_info_dict['output_name']
        full_output = os.path.join(output_dir, output_name)
        #Check to see if the output file already exists
        if os.path.exists(full_output):
            raise RuntimeError('Output file already exists: '+str(full_output))
        
        #Copy the image data
        logging.info('Copying file: '+str(image_to_copy))
        logging.info('Target location: '+str(full_output))
        copy_image(image_to_copy, full_output)

        #Create the sidecare .json file based on the .bxh
        output_name = bxh_info_dict['output_prefix']+'_'+bxh_info_dict['scan_label']+'.json'
        full_output = os.path.join(output_dir, output_name)
        create_anat_json(bxh_file, full_output)

    elif bxh_info_dict['scan_type'] == 'dwi':

        #Put together the output directory
        output_dir = output_dir_func(target_study_dir, bxh_info_dict, "dwi")

        #If the output directory does not exist, create it and
        #all upper directories.
        if not os.path.exists(output_dir):
            logging.info('Creating directory: '+str(output_dir))
            os.makedirs(output_dir)

        #Copy and rename the DWI data
        logging.info('Running copy_dwi on this .bxh.')

        #Copy the dwi image data
        image_to_copy = bxh_info_dict['orig_image']
        output_name = bxh_info_dict['output_name']
        full_output = os.path.join(output_dir, output_name)
        #Check to see if the output file already exists
        if os.path.exists(full_output):
            raise RuntimeError('Output file already exists: '+str(full_output))
        
        #Copy the image data
        logging.info('Copying file: '+str(image_to_copy))
        logging.info('Target location: '+str(full_output))
        copy_image(image_to_copy, full_output)

        #Create the sidecar .json file based on the .bxh
        output_name = bxh_info_dict['output_prefix']+'_'+bxh_info_dict['scan_label']+'.json'
        full_output = os.path.join(output_dir, output_name)
        create_dwi_json(bxh_file, full_output)

        #Create the bvecs and bvals files based on the .bxh
        logging.info('Running create_bvecs_bvals on this .bxh.')
        create_bvecs_bvals(bxh_file, bxh_info_dict, output_dir)
        
    elif bxh_info_dict['scan_type'] == 'notsupported':
        logging.info('Scan type not supported for: '+str(bxh_file))
    else:
        logging.error('Scan type not recognized; should be [bold,anat,dwi]: '+str(scan_type))
        raise RuntimeError('Scan type not recognized!')
        
    logging.info('----FINISH: convert_bxh----')


def auto_create_internal_info(bxh_file, events_files_dir, data_info, multi_bxh_info_dict):

    #Same as below, except pull all the info. from the file description
    #Directory and name of the bxh file
    bxh_dir, bxh_name = os.path.split(bxh_file)
    
    #Create dictionary entry for this bxh file
    this_entry_dict = {}

    #Load the contents of the bxh file into a dictionary
    with open(bxh_file) as fd:
        bxh_dict = xmltodict.parse(fd.read())
    
    #Get the image file associated with the bxh
    image_to_copy = os.path.join(bxh_dir, bxh_dict['bxh']['datarec']['filename'])
    #See if the actual image file is a .gz
    if not os.path.exists(image_to_copy):
        logging.info('Filename as stored in the bxh file cannot be found.')
        logging.info('Looking for .nii.gz...')
        if os.path.exists(str(image_to_copy)+'.gz'):
            logging.info('Found .gz version of image.')
            image_to_copy = str(image_to_copy)+'.gz'

    this_entry_dict['orig_image'] = image_to_copy

    #Get the description of the scan
    bxh_desc = bxh_dict['bxh']['acquisitiondata']['description']

    #Split the description to get scan type and various characteristics
    desc_parts = bxh_desc.split('_')

    #If the description is in the correct form, the parts should have
    #more than one entry.
    if len(desc_parts) == 1:
        logging.warning('bxh file description not in expected format!')
        logging.warning('bxh file: '+str(bxh_file))
        logging.warning('bxh description: '+str(bxh_desc))
        logging.warning('This bxh file will not be processed!')
        return multi_bxh_info_dict

    this_entry_dict['scan_type'] = desc_parts[0]
    this_entry_dict['scan_label'] = desc_parts[-1]
    this_entry_dict['sub'] = data_info['sub']
    this_entry_dict['ses'] = data_info['ses']
    this_entry_dict['bxh_desc'] = bxh_desc

    #Look for potential BIDS file name labels and add them to the entry dictionary if they are there
    for bids_label in ['task', 'acq', 'ce', 'rec', 'dir', 'run', 'mod', 'echo', 'IntendedFor']:
        for element in desc_parts[1:-1]:
            if element.split('-')[0] == bids_label:
                this_entry_dict[bids_label] = element.split('-')[-1]

    #Construct the output image file name
    naming_output = create_output_name(this_entry_dict)
    this_entry_dict['output_name'] = naming_output[0]
    this_entry_dict['output_prefix'] = naming_output[1]

    #Create the expected tsv events file name, if func
    if this_entry_dict['scan_type'] == 'func':
        this_entry_dict['tsv_file'] = os.path.join(events_files_dir, this_entry_dict['output_prefix']+'_events.tsv')

    #Set the output prefix
    if this_entry_dict['output_name'][-3:] == '.gz':
        image_ext = '.nii.gz'
    else:
        image_ext = '.nii'
    output_file_name = this_entry_dict['output_name'].split(image_ext)[0]
    #The prefix will be everything before the final file label (i.e. "bold", "events", etc.)
    this_entry_dict['output_prefix'] = "_".join(output_file_name.split('_')[:-1])

    #Add this bxh file's dictionary to the growing list.
    #Unless it's not supported.
    if this_entry_dict['scan_type'] in ['anat', 'func', 'dwi', 'fmap']:
        multi_bxh_info_dict[bxh_name] = this_entry_dict
    
    return multi_bxh_info_dict


def create_internal_info(bxh_file, ses_dict, multi_bxh_info_dict):

    #Directory and name of the bxh file
    bxh_dir, bxh_name = os.path.split(bxh_file)
    
    #Create dictionary entry for this bxh file
    this_entry_dict = {}

    #Load the contents of the bxh file into a dictionary
    with open(bxh_file) as fd:
        bxh_dict = xmltodict.parse(fd.read())
    
    #Get the image file associated with the bxh
    image_to_copy = os.path.join(bxh_dir, bxh_dict['bxh']['datarec']['filename'])
    #See if the actual image file is a .gz
    if not os.path.exists(image_to_copy):
        logging.info('Filename as stored in the bxh file cannot be found.')
        logging.info('Looking for .nii.gz...')
        if os.path.exists(str(image_to_copy)+'.gz'):
            logging.info('Found .gz version of image.')
            image_to_copy = str(image_to_copy)+'.gz'

    this_entry_dict['orig_image'] = image_to_copy

    #Get the description of the scan
    bxh_desc = bxh_dict['bxh']['acquisitiondata']['description']
    
    #Compare the description to those in the template file to determine type of scan
    here = os.path.dirname(os.path.realpath(__file__))  #returns the dir in which THIS file is
    template_file = os.path.join(here, 'info_field_files', 'psd_types.json')
    with open(template_file) as fd:
        template = json.loads(fd.read())
    #Make sure the scan description is in the template
    if bxh_desc not in template.keys():
        logging.error('Scan description not found in template file!')
        logging.error('Description: '+str(bxh_desc))
        logging.error('Template File: '+str(template_file))
        raise RuntimeError('Scan description not found in template file!')
    
    #Store the BIDS scan type (func, anat, dwi, fmap),
    #BIDS scan label (T1w, bold, etc.),
    #BIDS subject ID, and BIDS session label into the dictionary to return.
    this_entry_dict['scan_type'] = template[bxh_desc]['type']
    this_entry_dict['scan_label'] = scan_label = template[bxh_desc]['label']
    this_entry_dict['sub'] = ses_dict['sub']
    this_entry_dict['ses'] = ses_dict['ses']
    this_entry_dict['bxh_desc'] = bxh_desc

    ##TODO: This section can probably be rewritten as a single function. The
    ##different "match" functions can also probably be combined into one.

    #If it is a functional image, match the acquisition number with
    #an entry in the session info. file/dictionary.
    if this_entry_dict['scan_type'] == 'func':
        id_string = match_func(image_to_copy, ses_dict)
        for bids_label in ['task', 'acq', 'rec', 'run', 'echo', 'tsv_file']:
            if bids_label in ses_dict['funcs'][id_string].keys():
                this_entry_dict[bids_label] = ses_dict['funcs'][id_string][bids_label]

    #If it is an anatomical image, try to match the acquisition number
    #with an entry in the session info. file/dictionary. NOTE: this is
    #not required for anatomical scans.
    elif this_entry_dict['scan_type'] == 'anat':
        id_string = match_anat(image_to_copy, ses_dict)
        if id_string is not None:
            for bids_label in ['acq', 'ce', 'rec', 'run', 'mod']:
                if bids_label in ses_dict['anats'][id_string].keys():
                    this_entry_dict[bids_label] = ses_dict['anats'][id_string][bids_label]
        else:
            #If there is no rec value set in the session info file
            #but the image is a SCIC version of the original, set
            #the rec to reflect that.
            if 'SC' in bxh_desc:
                this_entry_dict['rec'] = 'SC'

    elif this_entry_dict['scan_type'] == 'fmap':
        id_string = match_fmap(image_to_copy, ses_dict)
        if id_string is not None:
            for bids_label in ['acq', 'ce', 'rec', 'dir', 'run', 'mod', 'IntendedFor']:
                if bids_label in ses_dict['fmaps'][id_string].keys():
                    this_entry_dict[bids_label] = ses_dict['fmaps'][id_string][bids_label]
                    ##NOTE: right now the IntendedFor info is NOT written to the final
                    ##.json file! It needs to be handled in create_dwi_json()!!!

    elif this_entry_dict['scan_type'] == 'dwi':
        id_string = match_dwi(image_to_copy, ses_dict)
        if id_string is not None:
            for bids_label in ['acq', 'ce', 'rec', 'run', 'mod']:
                if bids_label in ses_dict['dwis'][id_string].keys():
                    this_entry_dict[bids_label] = ses_dict['dwis'][id_string][bids_label]
    else:
        id_string = None

    #Construct the output image file name
    naming_output = create_output_name(this_entry_dict)
    this_entry_dict['output_name'] = naming_output[0]
    this_entry_dict['output_prefix'] = naming_output[1]

    #Set the output prefix
    if this_entry_dict['output_name'][-3:] == '.gz':
        image_ext = '.nii.gz'
    else:
        image_ext = '.nii'
    output_file_name = this_entry_dict['output_name'].split(image_ext)[0]
    #The prefix will be everything before the final file label (i.e. "bold", "events", etc.)
    this_entry_dict['output_prefix'] = "_".join(output_file_name.split('_')[:-1])

    #Add this bxh file's dictionary to the growing list.
    #Unless it's not supported.
    if this_entry_dict['scan_type'] != 'notsupported':
        multi_bxh_info_dict[bxh_name] = this_entry_dict

    return multi_bxh_info_dict
#####################

def create_output_name(bxh_info_dict):

    #This function takes as input a dictionary from the
    #multi_bxh_info_dict collection.

    output_prefix = 'sub-'+str(bxh_info_dict['sub'])+'_ses-'+str(bxh_info_dict['ses']) if bxh_info_dict['ses'] != "" else 'sub-'+str(bxh_info_dict['sub']) 

    output_suffix = ''
    for bids_label in ['task', 'acq', 'ce', 'rec', 'dir', 'run', 'echo', 'mod']:
        if bids_label in bxh_info_dict.keys():
            output_suffix = output_suffix+'_'+str(bids_label)+'-'+str(bxh_info_dict[bids_label])
    output_suffix = output_suffix+'_'+str(bxh_info_dict['scan_label'])

    if bxh_info_dict['orig_image'][-3:] == '.gz':
        output_ext = '.nii.gz'
    else:
        output_ext = '.nii'

    #Construct the output image file name
    output_name = output_prefix+output_suffix+output_ext

    #Construct the output prefix
    outname = output_name.split(output_ext)[0]
    return_prefix = "_".join(outname.split('_')[:-1])

    return [output_name, return_prefix]



def compare_output_names(multi_bxh_info_dict):

    #Compare output file names. If two bxh file entries have the same
    #output file name, try to fix this by including run numbers
    #in the name creation.
    logging.info('Making sure each output name is unique...')
    for bxh in multi_bxh_info_dict:
        #Entries for other files
        other_list = []
        for entry in multi_bxh_info_dict:
            if entry != bxh:
                other_list.append(entry)
        #Look for a repeated output name
        matching_list = [bxh]
        for other_bxh in other_list:
            if multi_bxh_info_dict[other_bxh]['output_name'] == multi_bxh_info_dict[bxh]['output_name']:
                matching_list.append(other_bxh)
                logging.info('Found identical output file names!')
                logging.info('First .bxh: '+str(bxh))
                logging.info('Second .bxh: '+str(other_bxh))
                logging.info('Attempting to fix this by adding run labels...')
        if len(matching_list) > 1:
            #Make sure run labels aren't already there
            for matching_bxh in matching_list:
                if 'run' in multi_bxh_info_dict[matching_bxh].keys():
                    logging.error('bxh files with conflicting output names have run labels in the bxh2bids session info file!')
                    logging.error('Check session info file to make sure there are not two acquisition numbers with identical entries!')
                    logging.error('Subject: '+str(multi_bxh_info_dict[bxh]['sub']))
                    logging.error('Session: '+str(multi_bxh_info_dict[bxh]['ses']))
                    raise RuntimeError('Duplicate info in session file? Sub: '+str(bidsid)+'; Ses: '+str(sesid))
            #Extract acquisition numbers from bxh file names
            logging.info('Extracting acquisition numbers from bxh file names...')
            num_list = []
            for matching_bxh in matching_list:
                bxh_number = os.path.splitext(bxh)[0][-3:]
                num_list.append(int(bxh_number))
            #Order the matching list by acquisition number
            ordered_bxh_list = [x for _,x in sorted(zip(num_list,matching_list), key=lambda pair: pair[0])]
            logging.info('Creating list of new run labels...')
            #Create a list of new run labels
            new_run_nums = range(1,len(ordered_bxh_list)+1)
            new_run_labels = []
            for element in new_run_nums:
                new_run_labels.append('%(num)02d' % {'num':element})
            #Put the new run labels into the bxh dictionaries that had matching names
            #and save the new output name into the dictionary.
            for [bxh, run_label] in zip(matching_list, new_run_labels):
                logging.info('Adding run number label to bxh: '+str(bxh))
                multi_bxh_info_dict[bxh]['run'] = run_label
                name_output = create_output_name(multi_bxh_info_dict[bxh])
                multi_bxh_info_dict[bxh]['output_name'] = name_output[0]
                multi_bxh_info_dict[bxh]['output_prefix'] = name_output[1]
                logging.info('Changing output file name for '+str(bxh)+' to '+str(multi_bxh_info_dict[bxh]['output_name']))
        else:
            logging.info('Did not find any identical output file names!')

    return multi_bxh_info_dict


def __set_logging(dataid, log_dir):

    logging.info('-----START: set_logging-----')
    
    #Make sure the passed log directory exists.
    #If not, create it.
    if not os.path.exists(log_dir):
        print('Log file directory cannot be found!')
        print('Creating it: '+str(log_dir))
        os.makedirs(log_dir)

    #Create log file
    time_stamp = str(time.localtime()[1])+str(time.localtime()[2])+str(time.localtime()[0])+str(time.localtime()[3])+str(time.localtime()[4])

    log_file = os.path.join(log_dir, 'bxh2bids_ses-'+str(dataid)+'_log_'+str(time_stamp)+'.txt')

    if os.path.isfile(log_file):
        raise RuntimeError('Log file already exists!?  They should be time-stamped down to the minute!')

    logFormatter = logging.Formatter('%(levelname)s:%(asctime)s:%(message)s')
    shortFormatter = logging.Formatter('%(levelname)s:%(message)s')
    rootLogger = logging.getLogger()

    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler(log_file)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.INFO)
    rootLogger.addHandler(fileHandler)
    
    logging.info('Created this log file.')


def __find_bxh_files(input_dir):

    bxh_list = []
    if os.path.exists(input_dir):
        logging.info('Looking for .bxh files in: '+str(input_dir))
        for element in os.listdir(input_dir):
            if element[-4:] == '.bxh':
                bxh_list.append({'bxhfile':os.path.join(input_dir, element), 'type':'anat'})
                logging.info('Found .bxh file: '+str(os.path.join(input_dir, element)))
    else:
        raise RuntimeError('Passed directory not found: '+str(input_dir))

    return bxh_list


def multi_autobxhtobids(dataid, data_info, source_study_dir, target_study_dir, events_files_dir, log_dir):

    __set_logging(dataid, log_dir)

    logging.info('-----START: multi_bxhtobids-----')
    
    #Make sure the passed study directory exists
    if not os.path.exists(source_study_dir):
        raise RuntimeError('Study directory cannot be found: ' + str(source_study_dir))

    #Make sure there is a Data directory.
    contents = os.listdir(source_study_dir)
    if 'Data' not in contents:
        raise RuntimeError('The study directory does not appear as expected: ' + str(source_study_dir))

    #Make sure the passed events_files_dir exists
    if not os.path.exists(events_files_dir):
        raise RuntimeError('Events Files directory cannot be found: ' + str(events_files_dir))

    #Record input arguments
    bidsid = data_info['sub']
    sesid = data_info['ses']

    #Record input arguments
    logging.info('--------------------------')
    logging.info('dataid: '+str(dataid))
    logging.info('bidsid: '+str(bidsid))
    logging.info('sesid: '+str(sesid))
    logging.info('source_study_dir: '+str(source_study_dir))
    logging.info('events_files_dir: '+str(events_files_dir))
    logging.info('target_study_dir: '+str(target_study_dir))
    logging.info('log_dir: '+str(log_dir))

    #Make sure dataid is in the format of a subject data directory
    r = re.compile('^\d\d\d\d\d\d\d\d_\d\d\d\d\d$')
    if r.match(dataid) is None:
        raise RuntimeError('dataid does not look like a data directory: '+str(dataid))
    
    #Look for the data directories in the Anat and Func directories
    anat_dir = os.path.join(source_study_dir, 'Data', 'Anat', dataid)
    func_dir = os.path.join(source_study_dir, 'Data', 'Func', dataid)
    if not os.path.exists(anat_dir):
        logging.info('No anatomy data directory found for id: '+str(dataid))
        anat_bxh_list = ''
    else:
        anat_bxh_list = __find_bxh_files(anat_dir)

    if not os.path.exists(func_dir):
        logging.info('No functional data directory found for id: '+str(dataid))
        func_bxh_list = ''
    else:
        func_bxh_list = __find_bxh_files(func_dir)

    bxh_list = anat_bxh_list + func_bxh_list

    #Construct dictionaries with information about all the bxh files
    multi_bxh_info_dict = {}
    for file_item in bxh_list:
        multi_bxh_info_dict = auto_create_internal_info(file_item['bxhfile'], events_files_dir, data_info, multi_bxh_info_dict)

    #Make sure the output file names are unique. If not, try to fix them.
    multi_bxh_info_dict = compare_output_names(multi_bxh_info_dict)

    #Process bxh files
    for file_item in bxh_list:
        bxh_file_name = os.path.split(file_item['bxhfile'])[-1]
        if bxh_file_name in multi_bxh_info_dict.keys():
            logging.info('Running convert_bxh on: '+str(file_item['bxhfile']))
            bxh_info_dict = multi_bxh_info_dict[bxh_file_name]
            convert_bxh(file_item['bxhfile'], bxh_info_dict, target_study_dir=target_study_dir)
        
    #Create dataset_description.json if it does not already exist
    logging.info('Running create_dataset_description().')
    create_dataset_description(target_study_dir)

    logging.info('-----FINISH: multi_bxhtobids-----')


def multi_bxhtobids(dataid, ses_dict, source_study_dir, target_study_dir, log_dir):
    

    __set_logging(dataid, log_dir)

    logging.info('-----START: multi_bxhtobids-----')
    
    #Make sure the passed study directory exists
    if not os.path.exists(source_study_dir):
        raise RuntimeError('Study directory cannot be found: ' + str(source_study_dir))

    #Make sure there is a Data directory.
    contents = os.listdir(source_study_dir)
    if 'Data' not in contents:
        raise RuntimeError('The study directory does not appear as expected: ' + str(source_study_dir))

    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']

    #Record input arguments
    logging.info('--------------------------')
    logging.info('dataid: '+str(dataid))
    logging.info('bidsid: '+str(bidsid))
    logging.info('sesid: '+str(sesid))
    logging.info('source_study_dir: '+str(source_study_dir))
    logging.info('target_study_dir: '+str(target_study_dir))
    logging.info('log_dir: '+str(log_dir))

    #Make sure dataid is in the format of a subject data directory
    r = re.compile('^\d\d\d\d\d\d\d\d_\d\d\d\d\d$')
    if r.match(dataid) is None:
        raise RuntimeError('dataid does not look like a data directory: '+str(dataid))
    
    #Look for the data directories in the Anat and Func directories
    anat_dir = os.path.join(source_study_dir, 'Data', 'Anat', dataid)
    func_dir = os.path.join(source_study_dir, 'Data', 'Func', dataid)
    if not os.path.exists(anat_dir):
        logging.info('No anatomy data directory found for id: '+str(dataid))
    else:
        anat_bxh_list = __find_bxh_files(anat_dir)

    if not os.path.exists(func_dir):
        logging.info('No functional data directory found for id: '+str(dataid))
    else:
        func_bxh_list = __find_bxh_files(func_dir)

    bxh_list = anat_bxh_list + func_bxh_list
    
    #Find .bxh files in the anat and func dirs
    # bxh_list = []
    # if os.path.exists(anat_dir):
    #     logging.info('Looking for .bxh files in: '+str(anat_dir))
    #     for element in os.listdir(anat_dir):
    #         if element[-4:] == '.bxh':
    #             bxh_list.append({'bxhfile':os.path.join(anat_dir, element), 'type':'anat'})
    #             logging.info('Found .bxh file: '+str(os.path.join(anat_dir, element)))
    # else:
    #     logging.info('No anatomy data directory found for id: '+str(dataid))
        
    # if os.path.exists(func_dir):
    #     logging.info('Looking for .bxh files in: '+str(func_dir))
    #     for element in os.listdir(func_dir):
    #         if element[-4:] == '.bxh':
    #             bxh_list.append({'bxhfile':os.path.join(func_dir, element), 'type':'func'})
    #             logging.info('Found .bxh file: '+str(os.path.join(func_dir, element)))
    # else:
    #     logging.info('No functional data directory found for id: '+str(dataid))
    
    #Construct dictionaries with information about all the bxh files
    multi_bxh_info_dict = {}
    for file_item in bxh_list:
        multi_bxh_info_dict = create_internal_info(file_item['bxhfile'], ses_dict, multi_bxh_info_dict)

    #The output file name stored for each bxh file should be unique.
    #If two of them are the same it means:
    #   1) The same anatomical scan was run multiple times and there is no
    #      information in the bxh2bids session info file about handling this.
    #   2) Multiple entries in the "funcs" portion of the session info file
    #      have the same task and run values.
    
    #Make sure the output file names are unique. If not, try to fix them.
    multi_bxh_info_dict = compare_output_names(multi_bxh_info_dict)

    #Process bxh files
    for file_item in bxh_list:
        bxh_file_name = os.path.split(file_item['bxhfile'])[-1]
        if bxh_file_name in multi_bxh_info_dict.keys():
            logging.info('Running convert_bxh on: '+str(file_item['bxhfile']))
            bxh_info_dict = multi_bxh_info_dict[bxh_file_name]
            convert_bxh(file_item['bxhfile'], bxh_info_dict, target_study_dir=target_study_dir)
            # convert_bxh(file_item['bxhfile'], ses_dict, target_study_dir=target_study_dir)
        
    #Create dataset_description.json if it does not already exist
    logging.info('Running create_dataset_description().')
    create_dataset_description(target_study_dir)

    logging.info('-----FINISH: multi_bxhtobids-----')
        
if __name__ == '__main__':
    ###TODO: handle input arguments
    #Check to make sure they're strings
    
    multi_bxh2bids(sys.argv)
    
    