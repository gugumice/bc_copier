#!/usr/bin/env python3
import json
import time
import logging
import argparse
import os,re
import tempfile
import cups
from  lib_prn import *
from  lib_bc import BarcodeReader
from lib_config import read_configuration
import threading
from string import Template

config ={}
RUN_DIR= os.path.dirname(os.path.realpath(__file__))
conn = None
label_tests = None
#Timer for setting bc scanning mode to default
bc_reader_reset = None
#Watchdog object
wd = None
barcode_reader = None

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)

def split_to_substrings(codes_list, max_length=30)-> list:
    '''
    Ensure, that multiple test ID's fit on barcode labels
    Returns substrings shorter than max_length
    '''
    substrings = []
    current_substring = []
    current_length = 0
    for code in codes_list:
        # Calculate the length of the current substring if we add this code (plus a comma if not the first code)
        new_length = current_length + len(code) + (1 if current_length > 0 else 0)

        # If adding this code exceeds the max length, finalize the current substring
        if new_length > max_length:
            substrings.append(','.join(current_substring))
            current_substring = [code]
            current_length = len(code)
        else:
            current_substring.append(code)
            current_length = new_length
    # Add the last accumulated substring
    if current_substring:
        substrings.append(','.join(current_substring))
    return substrings

def print_labels(zpl_text, printer_make='Zebra')->None:
    '''
    Sends labels to CUPS default printer
    '''
    global conn
    temp_file = tempfile.NamedTemporaryFile(prefix='kio_',suffix='.pdf', delete=False)
    with open(temp_file.name, 'w') as tf:
        tf.write(zpl_text)
    label_printer = conn.getDefault()
    print_job_id = conn.printFile(printer = label_printer, filename = temp_file.name,title = 'Report',options ={'print-color-mode': 'monochrome'})
    logging.info('Job: {} sent to printer'.format(print_job_id))

def make_select_sheet(label_data_file:str, select_template_file:str) -> str:
    '''
    Makes zpl code for printing labels for selecting copy mode
    '''
    label_data ={}
    zpl_text = ''
    with open(label_data_file) as f:
        label_data = json.loads(f.read())
    with open(select_template_file) as f:
        t = f.read()
    template = Template(t)
    for k,v in label_data.items():
        label_content = ','.join(v)
        label_content = split_to_substrings(v,28)
        while len(label_content) < 3:
            label_content.append('')
        zpl_text = '\n'.join([zpl_text, template.safe_substitute(label_content0=label_content[0],
                                                                 label_content1=label_content[1],
                                                                 label_content2=label_content[2],
                                                                 label_dept_name = config['dept_name'],
                                                                 label_barcode = k,
                                                                 label_copies = 1)])
    return(zpl_text)

def make_labels(barcode:str, label_tests = None, label_template_file = None)->str:
    '''
    Prints a copy of barcode
    '''
    global config
    with open(label_template_file) as f:
        t = f.read()
    template = Template(t)
    barcode = barcode.replace('#','')
    time_created = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    if label_tests is None:
        #No select code scanned so making strait copy
        label_dept_name = config['dept_name']
        zpl_text = template.safe_substitute(label_content0=time_created,
                                    label_content1='CC',
                                    label_content2='',
                                    label_barcode = barcode,
                                    label_dept_name = label_dept_name,
                                    label_copies = config['label_number_of_copies'])
    else:
        zpl_text = ''
        for test in label_tests[1]:
            zpl_text = zpl_text + '\n' + template.safe_substitute(label_content0=time_created,
                                                label_content1=label_tests[0],
                                                label_content2='',
                                                label_barcode = barcode,
                                                label_dept_name = test,
                                                label_copies = config['label_number_of_copies'])
    return(zpl_text)

def has_label_tests(barcode:str, label_data_file:str)->list:
    '''
    If label for selecting tests, get tests
    '''
    barcode = barcode.replace('#','')
    with open(label_data_file) as f:
        label_data = json.loads(f.read())
    if not barcode in label_data.keys():
        logging.info("Invalid barcode: {}".format(barcode))
        return(None)
    logging.debug('Mode set to: {}'.format(barcode))
    return([barcode, label_data[barcode]])

def bc_callback(barcode:str)->None:
    '''
    Calback called after barcode is scanned
    '''
    global config, conn, label_tests, bc_reader_reset
    logging.debug(f"Received barcode: {barcode}")
    if barcode == '#LAPA':
        zpl_text = make_select_sheet('{}/{}'.format(RUN_DIR,config['label_data_file']),'{}/{}'.format(RUN_DIR,config['label_template_file']))
        #print(zpl_text)
        print_labels(zpl_text = zpl_text)
        label_tests = None
    elif re.findall(config['barcode_regex'],barcode):
        zpl_text = make_labels(barcode, label_tests=label_tests, label_template_file = '{}/{}'.format(RUN_DIR,config['label_template_file']))
        print_labels(zpl_text = zpl_text)
        label_tests = None
    else:
        label_tests = has_label_tests(barcode, '{}/{}'.format(RUN_DIR,config['label_data_file']))
        bc_reader_reset = time.time()

def main():
    global config, conn, bc_reader_reset, wd, barcode_reader
    run_directory = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description="Barcode copier")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="file",
        help="Name config file. Default: bc.ini",
        default="{}/bc.ini".format(run_directory),
    )
    args = parser.parse_args()
    # Read from config file
    config = read_configuration(args.config)
    #set logging level from config
    if config['logging_level']:
        logger = logging.getLogger(__name__)
        logger.setLevel(config['logging_level'])
    #Set watchdog
    if config['watchdog_path']:
        try:
            wd = open(config['watchdog_path'], 'w')
            logging.info("Watchdog enabled on {}".format(config['watchdog_path']))
        except Exception as e:
            logging.error(e)
    else:
        logging.info("Watchdog disabled")
    #Check & set printer 
    conn = cups.Connection()
    setup_printer(conn=conn, include_schemes = config['include_schemes'], driver_list = config['driver_list'])
    #init barcode reader object
    barcode_reader = BarcodeReader(port=config['bc_port'],
                                   timeout=config['bc_reader_timeout'],
                                   callback=bc_callback,
                                   bounce=config['bc_reader_debounce'])
    while not barcode_reader.running:
        threading.Event().wait(1)
        logging.info('Starting reader')
        barcode_reader.start()
    while barcode_reader.running:
        #If bc_reader_reset timer exceeded, set to strait copy mode
        if bc_reader_reset and time.time() > bc_reader_reset + config['bc_reader_reset']:
            bc_reader_reset = None
            label_tests = None
            logging.info('Mode set to: copy')
            #Pat watchdog
        if wd is not None: print('1',file = wd, flush = True)
        threading.Event().wait(.5)
    #Stop watchdog
    if wd is not None: print('V',file = wd, flush = True)
    barcode_reader.stop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        barcode_reader.stop()
        #Stop watchdog if enabled
        if wd is not None:
            print('V',file = wd, flush = True)
        print("\nExiting")
