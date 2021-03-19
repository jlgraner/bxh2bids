

import json
import os, platform
import sys, logging
import tkinter
from tkinter.filedialog import asksaveasfile


def add_info(template_file, bxh_file, bxh_desc):

    logging.info('Loading PSD add GUI...')

    #Make sure psd type file is there
    if not os.path.exists(template_file):
        print('PSD info file not found!')
        print('File looked for: {}'.format(template_file))
        raise RuntimeError('PSD info file not found')

    bids_type, bids_label = get_info_gui(bxh_file, bxh_desc)


def get_info_gui(bxh_file, bxh_desc):

    window = tk.Tk()
    window.title('Get PSD Info.')

    frame_a = tk.Frame()
    bxh_file_sign_lbl = tk.Label(master=frame_a, text='BXH File: ')
    bxh_file_lbl = tk.Label(master=frame_a, text='{}'.format(bxh_file))
    bxh_desc_sign_lbl = tk.Label(master=frame_a, text='Acquisition Description: ')
    bxh_desc_lbl = tk.Label(master=frame_a, text='{}'.format(bxh_desc))
    bxh_file_sign_lbl.grid(row=0, column=0)
    bxh_file_lbl.grid(row=0, column=1)
    bxh_desc_sign_lbl.grid(row=1, column=0)
    bxh_desc_lbl.grid(row=1, column=1)

    frame_b = tk.Frame()
    bids_type_lbl = tk.Label(master=frame_b, text="BIDS type:")
    bids_type_ent = tk.Entry(master=frame_b)
    bids_label_lbl = tk.Label(master=frame_b, text="BIDS label:")
    bids_label_ent = tk.Entry(master=frame_b)
    submit = tk.Button(master=frame_b,text='Set PSD Info',command=add_psd_info)
    bids_type_lbl.grid(row=0, column=0, sticky='w')
    bids_type_ent.grid(row=0, column=1, sticky='w')
    bids_label_lbl.grid(row=1, column=0, sticky='w')
    bids_label_ent.grid(row=1, column=1, sticky='w')
    submit.grid(row=2, column=1)

    frame_a.pack(fill=tk.X, expand=True)
    frame_b.pack(fill=tk.X, expand=True)

    window.mainloop()


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
    here = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(here)
    import bxh2bids as b2b
    main()