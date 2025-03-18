#!/usr/bin/env python3
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
label_prefix = None
#Timer for setting bc scanning mode to default
bc_reader_reset = None
#Watchdog object
wd = None
barcode_reader = None
logging.basicConfig()

def print_labels(zpl_text)->int:
    '''
    Sends labels to CUPS default printer
    Returns: CUPS Job ID
    '''
    global conn
    temp_file = tempfile.NamedTemporaryFile(prefix='kio_',suffix='.pdf', delete=False)
    with open(temp_file.name, 'w') as tf:
        tf.write(zpl_text)
    label_printer = conn.getDefault()
    print_job_id = conn.printFile(printer = label_printer, filename = temp_file.name,title = 'Report',options ={'print-color-mode': 'monochrome'})
    return(print_job_id)

def make_labels(barcode:str, label_template_file:str)->str:
    '''
    Makes ZPL script to print labels
    Returns: ZPL II scropt for Zebra printers
    '''
    global config, label_prefix
    zpl_text = None
    try:
        with open(label_template_file) as f:
            t = f.read()
    except Exception as e:
        logging.error(e)
        return(None)
    label_template = Template(t)
    bc = list()
    #If AZTEC, seperate sample number from sample type, remove prefix
    if barcode.startswith('Az'):
        bc=barcode[2:].split(' ',1)
    #If CODE128, remove prefix set AZTEC to ''
    elif barcode.startswith('#'):
        bc.append(barcode[1:])
        bc.append(config['bc_default_sample_type'])
    if label_prefix:
        bc[0] = '{}{}'.format(label_prefix,bc[0])
    zpl_text = label_template.safe_substitute(label_title = config['label_title'],
                                              label_barcode = bc[0],
                                              label_aztec_code = bc[1],
                                              label_number_of_copies = config['label_number_of_copies'])

    return(zpl_text)

def bc_callback(barcode)->None:
    '''
    Calback after barcode is scanned
    '''
    global config, conn, label_prefix
    logging.debug(f'Barcode scanned: {barcode}')
    if re.fullmatch(config['bc_prefix_regex'], barcode):
        print(f'Prefix: {barcode}')
        label_prefix = barcode[1:]
    elif re.fullmatch(config['bc_regex'], barcode):
        # print(barcode, type(barcode))
        zpl_text = (make_labels(barcode, config['label_template_file']))
        logging.debug(zpl_text)
        print_job_id = print_labels(zpl_text)
        logging.info('Job: {} sent to printer'.format(print_job_id))
        label_prefix = None
    else:
        logging.error(f'Barcode rejected: {barcode}')

def main():
    global config, conn, bc_reader_reset, wd, barcode_reader
    run_directory = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description="Barcode copier")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="file",
        help="Configuration file. Default: bc.ini",
        default="{}/bc.ini".format(run_directory)
    )

    args = parser.parse_args()
    # Read from config file
    config = read_configuration(args.config)
    #set logging level from config
    if config['logging_level']:
        numeric_level = getattr(logging, config['logging_level'].upper(), logging.INFO)
        logging.basicConfig(level=numeric_level)
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
