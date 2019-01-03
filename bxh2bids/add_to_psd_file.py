

import json
import os, platform

def main():

    here = os.path.dirname(os.path.realpath(__file__))
    template_file = os.path.join(here, 'info_field_files', 'psd_types.json')

    print('Looking for PSD info file: {}'.format(template_file))

    #Make sure psd type file is there
    if not os.path.exists(template_file):
        print('PSD info file not found!')
        print('File looked for: {}'.format(template_file))
        raise RuntimeError('PSD info file not found')

    print('Fill in the following acquisition information.')

    #Get information to add to the psd type file
    bxh_desc, bids_type, bids_label = get_info()

    print('Reading PSD info file...')

    with open(template_file) as fd:
        template = json.loads(fd.read())
    #Make sure the scan description is not already in the template
    if bxh_desc in template.keys():
        print('Scan description passed is already in the psd type file!')
        print('bxh_desc: {}'.format(bxh_desc))
        print('psd type file: {}'.format(template_file))
        raise RuntimeError('Scan description already in psd type file')
    #Put the information into the full psd type dictionary
    template[bxh_desc] = {
                          "type":str(bids_type),
                          "label":str(bids_label)
                          }

    #Write the full dictionary back into the psd type file
    print('Re-writing template file...')
    with open(template_file, 'w') as fp:
        json.dump(template, fp, indent=4)


def get_info():
    #Collect input from user about the scan type to add
    if platform.python_version()[0] == '2':
        bxh_desc = str(raw_input('Scan Description from BXH: '))
        bids_type = str(raw_input('Scan type [anat, func, dwi, fmap, notsupported]: '))
        bids_label = str(raw_input('Scan BIDS label (e.g. bold, T1w, dwi...): '))
    elif platform.python_version()[0] == '3':
        bxh_desc = str(input('Scan Description from BXH: '))
        bids_type = str(input('Scan type [anat, func, dwi, fmap, notsupported]: '))
        bids_label = str(input('Scan BIDS label (e.g. bold, T1w, dwi...): '))
    else:
        print('Version of Python starts with neither a 2 nor a 3!?')
        print('Python version: {}'.format(platform.python_version()[0]))
        raise RuntimeError('Unexpected version of Python found!')

    return bxh_desc, bids_type, bids_label


if __name__ == '__main__':
    main()