#!/usr/bin/env python3
import os, socket, argparse, logging, re, json
from string import Template
import bcconf
from bclib import barCodeReader
from bcprn import kioPrinter
from zebra import Zebra

def init_bc():
    #Init logging
    if config['log_file'] is None:
        logging.basicConfig(format='%(asctime)s - %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - %(message)s',filename=config['log_file'],filemode='w',level=logging.INFO)
    #Init Watchdog
    global wdObj
    if config['watchdog_device'] is not None:
        try:
            wdObj=open(config['wd'],'w')
            logging.info('Watchdog enabled on {}'.format(config['watchdog_device']))
        except Exception as e:
            logging.error(e)
    else:
        logging.info('Watchdog disabled')

def print_label(bcode, template_file):    
    try:
        with open(template_file,'r') as f:
            templ=Template(f.read())
    except FileNotFoundError as e:
        logging.error(e)
        return(False)
    z=Zebra()
    #Find barcode printer queue
    for q in z.getqueues():
        for p in json.loads(config['printers']):
            if q.upper().startswith(p.upper()):
                print_queue=q
                break
    z.setqueue(print_queue)
    label_titles = json.loads(config['titles'])
    host_name = socket.gethostname()
    for k,v in label_titles.items():
        txt=templ.safe_substitute(lblTitle=k, hostName=host_name, barCode = bcode, numCopies=v)
        #print(txt)
        z.output(txt)
def main():
    global config
    run_directory = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description='EGL Barcode copier')
    parser.add_argument('-c','--config',
                        type=str,
                        metavar='file',
                        help='Configuration file. Default: bc.ini',
                        default='{}/bc.ini'.format(run_directory)
                        )
    args = parser.parse_args()
    #Read from config file
    config = bcconf.read_config(args.config)
    init_bc()
    print(config)
    bcrObj=barCodeReader(port=config['bc_port'], timeout = config['bc_timeout'],)
    bcrObj.start()
    prnObj=kioPrinter(json.loads(config['printers']),testpage=False)
    prnObj.start()
    prnObj=None
    
    #for print_queue in Zebra
    code_scanned=bc_prefix=''
    while bcrObj.running:
        #Pat watchdog
        if wdObj is not None: print('1',file = wdObj, flush = True)
        code_scanned = bcrObj.next()
        if len(code_scanned) == 0: continue #No code scannned - loop
        if len(re.findall(config['prefix_regex'],code_scanned))>0: #Check for prefix
            bc_prefix=code_scanned[1:]
            continue
        if len(re.findall(config['barcode_regex'],code_scanned))>0: #Check for barcode
            code_scanned = '{}{}'.format(bc_prefix,code_scanned)
            bc_prefix = ''
            print_label(code_scanned,'{}/{}'.format(run_directory,config['label_template']))

if __name__=='__main__':
    try:
        wdObj = None
        main()
    except KeyboardInterrupt:
        if wdObj is not None:
            print('V',file = wdObj, flush = True)
        print("\nExiting")