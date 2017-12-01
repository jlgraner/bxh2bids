

import os
import logging
import json, xmltodict


#This is meant to pull information from a bxh file and put it into a python
#dictionary that can then be written out into a BIDS image sidecar json file.
#
#In order to do this, there needs to be a link between the fields expected
#in the BIDS sidecar and the information in the bxh file. This link is in the
#form of the passed "json_file". This file must look like:
#
#{
#     "ManufacturersModelName": ["bxh", "acquisitiondata", "scannermodelname"],
#     "MagneticFieldStrength": ["bxh", "acquisitiondata", "magneticfield"],
#     "Manufacturer": ["bxh", "acquisitiondata", "scannermanufacturer"],
#     "DeviceSerialNumber": ["bxh", "acquisitiondata", "scannerserialnumber"],
#     "SoftwareVersions": ["bxh", "acquisitiondata", "softwareversions"],
#     "ReceiveCoilName": ["bxh", "acquisitiondata", "receivecoilname"],
#     "PulseSequenceType": ["bxh", "acquisitiondata", "description"],
#     "EffectiveEchoSpacing": ["bxh", "acquisitiondata", "echospacing"],
#     "EchoTime": ["bxh", "acquisitiondata", "te"],
#     "InversionTime": ["bxh", "acquisitiondata", "ti"],
#     "FlipAngle": ["bxh", "acquisitiondata", "flipangle"],
#     "InstitutionName": ["bxh", "acquisitiondata", "institution"]
# }
#
#That is, each field name is the field name of the item expected in the BIDS
#sidecare file and the values are lists of keys that will locate the associated
#values in a bxh file.
#
#bxh_pick() can receive this link in one of two formats:
#   1) The full path/name of a bxh file, which it will then read in as a dictionary
#      using xmltodict (NOTE: bxh files are in XML format).
#   2) A python dictionary of the contents of the bxh file.


def bxh_pick(json_file, bxh_file=None, bxh_as_dict=None):

    logging.info('-STARTING: bxh_pick-')

    if bxh_file is not None:
        logging.info('Trying to load passed bxh file.')
        if not os.path.exists(bxh_file):
            logging.error('Passed bxh file cannot be found!')
            logging.error('Looked for file: '+str(bxh_file))
            raise RuntimeError('Passed bxh file could not be found.')
        with open(bxh_file) as fd:
            bxh_dict = xmltodict.parse(fd.read())
    else:
        if bxh_as_dict is None:
            raise RuntimeError('Both bxh_file and bxh_as_dict are None!')
        bxh_dict = bxh_as_dict

    out_dict = {}

    #Check to make sure the passed file exists
    if not os.path.exists(json_file):
        logging.error('Cannot find passed json file!')
        raise RuntimeError('Looked for and could not find: '+str(json_file))

    with open(json_file) as fd:
        template = json.loads(fd.read())

    #template will be a dictionary in which the keys are
    #field names to be written to a BIDS sidecar json file
    #and the values are the field names in which the corresponding
    #values are saved in the bxh file.

    for key in template.keys():
        try:
            this_item = bxh_dict
            bxh_field_location = template[key]['location']
            bids_style = template[key]['BIDSstyle']
            #Go through the elements in the list of bxh fields and keep "digging"
            #until we get to the final value.
            for element in bxh_field_location:
                this_item = this_item[element]
            #The keys in the input json file need to be the same as those expected
            #in the BIDS sidecar file.
            if bids_style == 'string':
                out_dict[key] = str(this_item)
            elif bids_style == 'float':
                out_dict[key] = float(this_item)
            elif bids_style == 'int':
                out_dict[key] = int(this_item)
            else:
                logging.warning('Unkown BIDS type found in field link json!')
                logging.warning('File: '+str(json_file))
                logging.warning('Item Key: '+str(key))
                logging.warning('BIDSstyle: '+str(bids_style))
                logging.warning('Just using original type!')
                out_dict[key] = this_item
        except KeyError:
            logging.info('Field not found in bxh: '+str(key))

    logging.info('-FINISHED: bxh_pick-')

    return out_dict