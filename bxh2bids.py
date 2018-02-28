
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
                logging.error('BIDS ID: '+str(bidsid))
                logging.error('Sess ID: '+str(sesid))
                raise RuntimeError('Functional file matched with > 1 id string!')
            taskid = ses_dict['funcs'][element]['task']
            runid = ses_dict['funcs'][element]['run']
            func_id_string = element
    if not file_identified:
        logging.error('Func file not matchted with id string!')
        logging.error('File name: '+str(image_to_copy))
        logging.error('BIDS ID: '+str(bidsid))
        logging.error('Sess ID: '+str(sesid))
        raise RuntimeError('Functional file cannot be matched with id string!')

    # #Pull information from the func id structure
    # for label in ses_dict['funcs'][func_id_string]:
    #     if label in ['task', 'acq', 'rec', 'run', 'echo']: #These are BIDS-allowable labels
    #         output_prefix = output_prefix+'_'+str(label)+'-'+str(ses_dict['funcs'][func_id_string][label])

    logging.info('--FINISHED: match_func--')

    return func_id_string

def copy_func(image_to_copy, scan_label, ses_dict, output_dir):
    
    logging.info('---START: copy_func---')
    
    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']
    
    #If the output directory does not exist, create it and
    #all upper directories.
    if not os.path.exists(output_dir):
        logging.info('Creating directory: '+str(output_dir))
        os.makedirs(output_dir)

    #Create the output file name based on the id structure in hopes and dreams.
    func_id_string = match_func(image_to_copy, ses_dict)

    #Start the output name
    output_prefix = 'sub-'+str(bidsid)+'_ses-'+str(sesid)

    #Pull information from the func id structure
    for label in ses_dict['funcs'][func_id_string]:
        if label in ['task', 'acq', 'rec', 'run', 'echo']: #These are BIDS-allowable labels
            output_prefix = output_prefix+'_'+str(label)+'-'+str(ses_dict['funcs'][func_id_string][label])

    ##TODO: clean this up!
    #Get the input file type
    if image_to_copy[-3:] == '.gz':
        file_type = '.nii.gz'
    else:
        file_type = '.nii'

    #Copy the func image data
    output_name = str(output_prefix)+'_'+str(scan_label)+file_type
    full_output = os.path.join(output_dir, output_name)
    #Check to see if the output file already exists
    if os.path.exists(full_output):
        raise RuntimeError('Output file already exists: '+str(full_output))
    
    #Copy the image data
    logging.info('Copying file: '+str(image_to_copy))
    logging.info('Target location: '+str(full_output))
    shutil.copy2(image_to_copy, full_output)
    
    #Copy a .tsv file if it exists
    func_dict = ses_dict['funcs'][func_id_string]
    if 'tsv_file' in func_dict.keys():
        if not os.path.exists(func_dict['tsv_file']):
            raise RuntimeError('tsv_file cannot be found: '+str(func_dict['tsv_file']))
        tsv_output_name = str(output_prefix)+'_events.tsv'
        tsv_full_output = os.path.join(output_dir, tsv_output_name)
        #Check to see if the output exists already
        if os.path.exists(tsv_full_output):
            raise RuntimeError('Output file already exists: '+str(tsv_full_output))
        tsv_to_copy = func_dict['tsv_file']
        logging.info('Copying file: '+str(tsv_to_copy))
        logging.info('Target location: '+str(tsv_full_output))
        shutil.copy2(tsv_to_copy, tsv_full_output)

    logging.info('---FINISHED: copy_func---')

def copy_anat(image_to_copy, scan_label, ses_dict, output_dir, other_label=''):
    
    logging.info('---START: copy_anat---')
    
    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']
    
    #If the output directory does not exist, create it and
    #all upper directories.
    if not os.path.exists(output_dir):
        logging.info('Creating directory: '+str(output_dir))
        os.makedirs(output_dir)
    
    ##TODO: clean this up! These strings should not be hard-coded in the script!##
    #Get the input file type
    if image_to_copy[-3:] == '.gz':
        file_type = '.nii.gz'
    else:
        file_type = '.nii'

    #Copy the anatomy image data
    output_name = 'sub-'+str(bidsid)+'_ses-'+str(sesid)+other_label+'_'+scan_label+file_type
    full_output = os.path.join(output_dir, output_name)
    #Check to see if the output file already exists
    if os.path.exists(full_output):
        raise RuntimeError('Output file already exists: '+str(full_output))
    
    #Copy the image data
    logging.info('Copying file: '+str(image_to_copy))
    logging.info('Target location: '+str(full_output))
    shutil.copy2(image_to_copy, full_output)
    
    logging.info('---FINISHED: copy_anat---')

    
def copy_dwi(image_to_copy, scan_label, ses_dict, output_dir):

    logging.info('---START: copy_dwi---')
    
    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']
    
    #If the output directory does not exist, create it and
    #all upper directories.
    if not os.path.exists(output_dir):
        logging.info('Creating directory: '+str(output_dir))
        os.makedirs(output_dir)

    ##TODO: clean this up! These strings should not be hard-coded here
    #Get the input file type
    if image_to_copy[-3:] == '.gz':
        file_type = '.nii.gz'
    else:
        file_type = '.nii'

    #Copy the dwi image data
    output_name = 'sub-'+str(bidsid)+'_ses-'+str(sesid)+'_'+scan_label+file_type
    full_output = os.path.join(output_dir, output_name)
    #Check to see if the output file already exists
    if os.path.exists(full_output):
        raise RuntimeError('Output file already exists: '+str(full_output))
    
    #Copy the image data
    logging.info('Copying file: '+str(image_to_copy))
    logging.info('Target location: '+str(full_output))
    shutil.copy2(image_to_copy, full_output)
    
    logging.info('---FINISHED: dwi_func---')


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
            slice_order_list = element['datapoints']['#text']
            num_slices = float(element['size'])
    factor = tr/num_slices
    st = []
    for s in slice_order_list.split(' '):
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
    func_field_file = os.path.join(here, 'info_field_files', 'dwi_info_fields.json')
    if not os.path.exists(func_field_file):
        logging.error('DWI image sidecar template file cannot be found!')
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

    out_string = json.dumps(out_dict, indent=4)

    logging.info('Writing sidecar func file: '+str(full_output))
    with open(full_output, 'w') as out_file:
        out_file.write(out_string)

    logging.info('---FINISHED: create_dwi_json---')


def create_bvecs_bvals(bxh_file, ses_dict, output_dir):
    # open DWI bxh file, read b-vector and b-value information 
    # and write into BIDS formatted .bvec and .bval files
    #
    # John Powers, LaBar Lab, Duke University, Nov. 2017
    
    logging.info('---START: create_bvecs_bvals---')

    # get subject and session info for file names
    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']
    
    # read in the bxh_file using xmltodict
    logging.info('')
    with open(bxh_file) as dwi_bxh:
        bxh_contents = xmltodict.parse(dwi_bxh.read())
    
    # generate .bval file name
    bvals_output_name = 'sub-' + str(bidsid) + '_ses-' + str(sesid) + '_dwi.bval'
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

    
    # generate .bvec file name
    bvecs_output_name = 'sub-' + str(bidsid) + '_ses-' + str(sesid) + '_dwi.bvec'
    bvecs_full_output = os.path.join(output_dir, bvecs_output_name)
    
    # create .bvec file and write x, y, and z components as separate rows
    with open(bvecs_full_output, "w") as bvecs:
        bvecs.write(bvec_x_line + "\n")
        bvecs.write(bvec_y_line + "\n")
        bvecs.write(bvec_z_line)

    logging.info('---FINISH: create_bvecs_bvals---')

def convert_bxh(bxh_file, ses_dict, target_study_dir=None):
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
    bxh_dir = os.path.split(bxh_file)[0]
    
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
    
    #Get the description of the scan
    bxh_desc = bxh_dict['bxh']['acquisitiondata']['description']
    
    #Compare the description to those in the template file to determine type of scan
    here = os.path.dirname(os.path.realpath(__file__))  #returns the dir in which THIS file is
    template_file = os.path.join(here, 'psd_types.json')
    with open(template_file) as fd:
        template = json.loads(fd.read())
    #Make sure the scan description is in the template
    if bxh_desc not in template.keys():
        logging.error('Scan description not found in template file!')
        logging.error('Description: '+str(bxh_desc))
        logging.error('Template File: '+str(template_file))
        raise RuntimeError('Scan description not found in template file!')
    
    scan_type = template[bxh_desc]['type']
    scan_label = template[bxh_desc]['label']
    logging.info('Scan type: '+str(scan_type))
    logging.info('Scan label: '+str(scan_label))
    
    bidsid = ses_dict['sub']
    sesid = ses_dict['ses']

    if scan_type == 'func':

        #Put together the output directory
        output_dir = os.path.join(target_study_dir, 'sub-'+str(bidsid), 'ses-'+str(sesid), 'func')

        #Copy and rename the functional data
        logging.info('Running copy_func on this .bxh.')
        copy_func(image_to_copy, scan_label, ses_dict, output_dir)

        #Create the sidecar .json file based on the .bxh
        func_id_string = match_func(image_to_copy, ses_dict)

        #Start the output name
        output_prefix = 'sub-'+str(bidsid)+'_ses-'+str(sesid)

        #Pull information from the func id structure
        for label in ses_dict['funcs'][func_id_string]:
            if label in ['task', 'acq', 'rec', 'run', 'echo']: #These are BIDS-allowable labels
                output_prefix = output_prefix+'_'+str(label)+'-'+str(ses_dict['funcs'][func_id_string][label])

        full_output = os.path.join(output_dir, output_prefix+'_'+str(scan_label)+'.json')
        create_bold_json(bxh_file, full_output)

    elif scan_type == 'anat':

        #Put together the output directory
        output_dir = os.path.join(target_study_dir, 'sub-'+str(bidsid), 'ses-'+str(sesid), 'anat')

        ##TODO: clean this up! This should not be hard-coded into the script!!!##
        #Check to see if the image has been through SCIC
        if 'SC:' in bxh_desc:
            other_label = '_rec-SC'
        else:
            other_label = ''

        #Copy and rename the anatomical data
        logging.info('Running copy_anat on this .bxh.')
        copy_anat(image_to_copy, scan_label, ses_dict, output_dir, other_label=other_label)

        #Create the sidecare .json file based on the .bxh
        output_file = 'sub-'+str(bidsid)+'_ses-'+str(sesid)+other_label+'_'+scan_label+'.json'
        full_output = os.path.join(output_dir, output_file)
        create_anat_json(bxh_file, full_output)

    elif scan_type == 'dwi':

        #Put together the output directory
        output_dir = os.path.join(target_study_dir, 'sub-'+str(bidsid), 'ses-'+str(sesid), 'dwi')

        #Copy and rename the DWI data
        logging.info('Running copy_dwi on this .bxh.')
        copy_dwi(image_to_copy, scan_label, ses_dict, output_dir)

        #Create the sidecar .json file based on the .bxh
        output_file = 'sub-'+str(bidsid)+'_ses-'+str(sesid)+'_'+str(scan_label)+'.json'
        full_output = os.path.join(output_dir, output_file)
        create_dwi_json(bxh_file, full_output)

        #Create the bvecs and bvals files based on the .bxh
        logging.info('Running create_bvecs_bvals on this .bxh.')
        create_bvecs_bvals(bxh_file, ses_dict, output_dir)
        
    elif scan_type == 'notsupported':
        logging.info('Scan type not supported for: '+str(bxh_file))
    else:
        logging.error('Scan type not recognized; should be [bold,anat,dwi]: '+str(scan_type))
        raise RuntimeError('Scan type not recognized!')
        
    logging.info('----FINISH: convert_bxh----')

def multi_bxhtobids(dataid, ses_dict, source_study_dir, target_study_dir, log_dir):
    
    logging.info('-----START: multi_bxhtobids-----')
    
    #Make sure the passed study directory exists
    if not os.path.exists(source_study_dir):
        raise RuntimeError('Study directory cannot be found: ' + str(source_study_dir))
    
    #Make sure the passed log directory exists
    if not os.path.exists(log_dir):
        raise RuntimeError('Log file directory cannot be found: ' + str(log_dir))

    #Make sure there is a Data directory.
    contents = os.listdir(source_study_dir)
    if 'Data' not in contents:
        raise RuntimeError('The study directory does not appear as expected: ' + str(source_study_dir))

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
    
    #Find .bxh files in the anat and func dirs
    bxh_list = []
    if os.path.exists(anat_dir):
        logging.info('Looking for .bxh files in: '+str(anat_dir))
        for element in os.listdir(anat_dir):
            if element[-4:] == '.bxh':
                bxh_list.append({'bxhfile':os.path.join(anat_dir, element), 'type':'anat'})
                logging.info('Found .bxh file: '+str(os.path.join(anat_dir, element)))
    else:
        logging.info('No anatomy data directory found for id: '+str(dataid))
        
    if os.path.exists(func_dir):
        logging.info('Looking for .bxh files in: '+str(func_dir))
        for element in os.listdir(func_dir):
            if element[-4:] == '.bxh':
                bxh_list.append({'bxhfile':os.path.join(func_dir, element), 'type':'func'})
                logging.info('Found .bxh file: '+str(os.path.join(func_dir, element)))
    else:
        logging.info('No functional data directory found for id: '+str(dataid))
    
    #Process bxh files
    for file_item in bxh_list:
        logging.info('Running convert_bxh on: '+str(file_item['bxhfile']))
        
        convert_bxh(file_item['bxhfile'], ses_dict, target_study_dir=target_study_dir)
        
    #Create dataset_description.json if it does not already exist
    logging.info('Running create_dataset_description().')
    create_dataset_description(target_study_dir)

    logging.info('-----FINISH: multi_bxhtobids-----')
        
if __name__ == '__main__':
    ###TODO: handle input arguments
    #Check to make sure they're strings
    
    multi_bxh2bids(sys.argv)
    
    