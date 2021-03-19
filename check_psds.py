

import json
import os, getopt, re
import sys, logging
import tkinter as tk
import xmltodict



class psd_gui():
    def __init__(self, bxh_file='None passed', bxh_desc='None passed'):
        self.bxh_file = bxh_file
        self.bxh_desc = bxh_desc

        self.window = tk.Tk()
        self.window.title('Get PSD Info.')

        self.frame_a = tk.Frame()
        #Create display of bxh file and bxh description
        self.bxh_file_sign_lbl = tk.Label(master=self.frame_a, text='BXH File: ')
        self.bxh_file_lbl = tk.Label(master=self.frame_a, text='{}'.format(self.bxh_file))
        self.bxh_desc_sign_lbl = tk.Label(master=self.frame_a, text='Acquisition Description: ')
        self.bxh_desc_lbl = tk.Label(master=self.frame_a, text='{}'.format(self.bxh_desc))
        self.bxh_file_sign_lbl.grid(row=0, column=0)
        self.bxh_file_lbl.grid(row=0, column=1)
        self.bxh_desc_sign_lbl.grid(row=1, column=0)
        self.bxh_desc_lbl.grid(row=1, column=1)

        self.frame_b = tk.Frame()

        #Create type dropdown menu
        self.bids_type_lbl = tk.Label(master=self.frame_b, text="BIDS type:")
        self.typevar = tk.StringVar(self.window)
        self.typevar.set('anat')
        typechoices = ['dwi', 'anat', 'func', 'notsupported']
        self.bids_type_drop = tk.OptionMenu(self.frame_b, self.typevar, *typechoices)

        #Create label dropdown menu
        self.bids_label_lbl = tk.Label(master=self.frame_b, text="BIDS label:")
        self.labelvar = tk.StringVar(self.window)
        self.labelvar.set('T1w')
        labelchoices = ['bold', 'LOC', 'T1w', 'dwi', 'b0', 'T2w']
        self.bids_label_drop = tk.OptionMenu(self.frame_b, self.labelvar, *labelchoices)

        self.submit = tk.Button(master=self.frame_b,text='Set PSD Info',command=self.gui_submit_btn)
        self.bids_type_lbl.grid(row=0, column=0, sticky='w')
        self.bids_type_drop.grid(row=0, column=1, sticky='w')
        self.bids_label_lbl.grid(row=1, column=0, sticky='w')
        self.bids_label_drop.grid(row=1, column=1, sticky='w')
        self.submit.grid(row=2, column=1)

        self.frame_a.pack(fill=tk.X, expand=True)
        self.frame_b.pack(fill=tk.X, expand=True)

    def run_loop(self):
        self.window.mainloop()

    def gui_submit_btn(self):
        #Save the entered bids type and bids label
        self.bids_type = self.typevar.get()
        self.bids_label = self.labelvar.get()

        #Delete the GUI
        self.window.destroy()



def create_bxh_list(source_study_dir, dataid):

    logging.debug('-----START: create_bxh_list-----')
    logging.info('Looking for bxh files...')
    
    #Make sure the passed study directory exists
    if not os.path.exists(source_study_dir):
        raise RuntimeError('Study directory cannot be found: ' + str(source_study_dir))

    #Make sure there is a Data directory.
    contents = os.listdir(source_study_dir)
    if 'Data' not in contents:
        raise RuntimeError('The study directory does not appear as expected: ' + str(source_study_dir))

    #Record input arguments
    logging.info('--------------------------')
    logging.info('source_study_dir: '+str(source_study_dir))
    logging.info('dataid: '+str(dataid))
    logging.info('--------------------------')

    #Make sure dataid is in the format of a subject data directory
    r = re.compile('^\d\d\d\d\d\d\d\d_\d\d\d\d\d$')
    if r.match(dataid) is None:
        raise RuntimeError('dataid does not look like a data directory: '+str(dataid))
    
    #Look for the data directories in the Anat and Func directories
    anat_dir = os.path.join(source_study_dir, 'Data', 'Anat', dataid)
    func_dir = os.path.join(source_study_dir, 'Data', 'Func', dataid)
    if not os.path.exists(anat_dir):
        logging.info('No anatomy data directory found for id: '+str(dataid))
        anat_bxh_list = []
    else:
        anat_bxh_list = b2b.__find_bxh_files(anat_dir)

    if not os.path.exists(func_dir):
        logging.info('No functional data directory found for id: '+str(dataid))
        func_bxh_list = []
    else:
        func_bxh_list = b2b.__find_bxh_files(func_dir)

    bxh_list = anat_bxh_list + func_bxh_list

    return bxh_list



def get_info_gui(bxh_file, bxh_desc):
    #Create GUI object
    gui = psd_gui(bxh_file, bxh_desc)
    #Start the GUI
    gui.run_loop()
    #Exctract the information from the GUI object
    bids_type = gui.bids_type
    bids_label = gui.bids_label

    return bids_type, bids_label


def main(argv):

    write_flag = 0

    #Deal with passed arguments
    try:
        opts, args = getopt.getopt(argv, "hi:d:", ['idir=', 'dataid='])
    except getopt.GetoptError:
        print('check_psds.py -i <input_dir> -d <dataid>')
        raise RuntimeError('Check passed args...')

    for opt, arg in opts:
        if opt == '-h':
            print('check_psds.py -i <input_dir> -d <dataid>')
            sys.exit()
        elif opt in ('-i', '--idir'):
            source_study_dir = str(arg)
        elif opt in ('-d', '--dataid'):
            dataid = str(arg)

    here = os.path.dirname(os.path.realpath(__file__))
    template_file = os.path.join(here, 'info_field_files', 'psd_types.json')

    print('Looking for PSD info file: {}'.format(template_file))

    #Make sure psd type file is there
    if not os.path.exists(template_file):
        print('PSD info file not found!')
        print('File looked for: {}'.format(template_file))
        raise RuntimeError('PSD info file not found')

    #Get list of bxh files
    bxh_list = create_bxh_list(source_study_dir, dataid)

    #Read in the psd template file
    logging.info('Reading PSD info file...')
    with open(template_file) as fd:
        template = json.loads(fd.read())

    for bxh_file in bxh_list:
        logging.info('Checking bxh file: {}'.format(bxh_file['bxhfile']))
        #Load the contents of the bxh file into a dictionary
        with open(bxh_file['bxhfile']) as fd:
            bxh_dict = xmltodict.parse(fd.read())

        #Get the description of the scan
        bxh_desc = bxh_dict['bxh']['acquisitiondata']['description']
        
        #See if the scan description is already in the template
        if bxh_desc in template.keys():
            logging.info('Scan description already in PSD type file.')
            logging.info('bxh_desc: {}'.format(bxh_desc))
        else:
            logging.info('Scan description not found in PSD type file.')
            logging.info('bxh_desc: {}'.format(bxh_desc))
            logging.info('Opening GUI for input...')
            bids_type, bids_label = get_info_gui(bxh_file['bxhfile'], bxh_desc)

            logging.info('BIDS type received: {}'.format(bids_type))
            logging.info('BIDS label received: {}'.format(bids_label))

            #Put the information into the full psd type dictionary
            template[bxh_desc] = {
                                  "type":str(bids_type),
                                  "label":str(bids_label)
                                  }
            write_flag = 1

    #Write the full dictionary back into the psd type file
    if write_flag:
        logging.info('Re-writing template file...')
        with open(template_file, 'w') as fp:
            json.dump(template, fp, indent=4)
    else:
        logging.info('All scan descriptions already known.')


if __name__ == '__main__':
    here = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(here)
    import bxh2bids as b2b

    logging.basicConfig(level=logging.INFO)

    main(sys.argv[1:])