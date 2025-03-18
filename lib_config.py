#!/usr/bin/env python3
import configparser
import logging
import os

def read_configuration(config_file:str) -> dict:
    '''
    Reads configuration file, sets default values if missing
 
    Args:
        configuration file

    Returns dict with configuration settings
    '''
    # Default config values
    bcr_config = {
        'watchdog_path' :None,
        'label_title': 'EGL',
        'logging_level': 'INFO',
        'label_template_file': 'label_template.txt',
        'label_number_of_copies': 1,
        'bc_port': '/dev/ttyACM0',
        'bc_reader_timeout': 1,
        'bc_reader_debounce': 1.5,
        'bc_reader_reset': 60,
        'include_schemes': ['usb'],
        'driver_list': {'Zebra':'Raw'},
        'barcode_regex': '^#\d{7,9}$',
        'barcode_prefix_regex': '^#\d{2}$',
        'bc_default_sample_type': ''
        }

    if not os.path.isfile(config_file):
        logging.critical("Config file {} does not exist!".format(config_file))
        return(None)
    config = configparser.ConfigParser(allow_no_value=True,
                        converters={'list': lambda x: [int(i.strip()) for i in x.split(',')],
                                    'list_s' : lambda x: [i.strip() for i in x.split(',')]})
    config.read(config_file)

    #Get values from ini file line by line to catch errors in config file
    commands = (
        "bcr_config['watchdog_path'] = config.get('WATCHDOG','watchdog_path')",
        "bcr_config['logging_level'] = config.get('LOGGING','logging_level')",
        "bcr_config['label_title'] = config.get('INFO','label_title')",
        "bcr_config['label_template_file'] = config.get('LABEL','label_template_file')",
        "bcr_config['label_number_of_copies'] = config.getint('LABEL','label_number_of_copies')",
        "bcr_config['bc_reader_port'] = config.get('BARCODE','bc_reader_port')",
        "bcr_config['bc_reader_timeout'] = config.getfloat('BARCODE','bc_reader_timeout')",
        "bcr_config['bc_reader_debounce'] = config.getfloat('BARCODE','bc_reader_debounce')",
        "bcr_config['bc_regex'] = config.get('BARCODE','bc_regex')",
        "bcr_config['bc_prefix_regex'] = config.get('BARCODE','bc_prefix_regex')",
        "bcr_config['bc_default_sample_type'] = config.get('BARCODE','bc_default_sample_type')",
        "bcr_config['prn_driver_list'] = config.getlist_s('PRINTER','prn_driver_list')",
        "bcr_config['prn_include_schemes'] = config.getlist_s('PRINTER','prn_include_schemes')",
    )

    for command in commands:
        try:
            exec(command)
        except Exception as e:
            logging.error(e)
    return(bcr_config)

def main():
    config_file = 'bc.ini'
    run_directory= os.path.dirname(os.path.realpath(__file__))
    full_path = '{}/{}'.format(run_directory,config_file)
    c = read_configuration(full_path)
    print(c)

if __name__ == '__main__':
    main()
