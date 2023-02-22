#!/usr/bin/env python3
import configparser
import logging
import os
#, json

def read_config(filename):
    bc_config = {
        'log_file': '/home/pi/kiosk.log',
        'prefix_regex': '^#\d{1,2}$',
        'barcode_regex': '^\d{7,9}$',
        'bc_port': '/dev/ttyACM0',
        'bc_timeout': .5,
        'watchdog_device' : '/dev/watchdog',
        'printers':  {"Zebra": "Raw"},
        'titles': {"EGL": 1,"EGL2":2},
        'label_template': 'lblTemplate.txt'
    }
    if not os.path.isfile(filename):
        logging.critical("Config file {} does not exist!".format(filename))
        return(None)
    cf = configparser.ConfigParser(allow_no_value=True,
                            converters={'list': lambda x: [int(i.strip()) for i in x.split(',')],
                                        'list_s' : lambda x: [i.strip() for i in x.split(',')]})
    cf.read(filename)
    try:
        bc_config['log_file'] = cf.get('BARCODE','log_file')
        bc_config['prefix_regex'] = cf.get('BARCODE','prefix_regex')
        bc_config['barcode_regex'] = cf.get('BARCODE','barcode_regex')
        bc_config['bc_port'] = cf.get('BARCODE','bc_port')
        bc_config['bc_timeout'] = cf.getfloat('BARCODE','bc_timeout')
        bc_config['watchdog_device'] = cf.get('BARCODE','watchdog_device')
        bc_config['printers'] = cf.get('BARCODE','printers')
        bc_config['titles'] = cf.get('BARCODE','titles')
        bc_config['label_template'] = cf.get('BARCODE','label_template')
    except configparser.Error as e:
        logging.error(e)
   
    return(bc_config)

def main():
    f = '{}/{}'.format(os.getcwd(),'bc.ini')
    cfg = read_config(f)
    print(cfg)

if __name__ == '__main__':
    main()
