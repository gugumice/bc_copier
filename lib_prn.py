#!/usr/bin/env python3
import cups
import logging

#sudo systemctl disable cups-browsed

def current_printer_connected(conn: cups.Connection, include_schemes: list = ['usb','driverless'])-> bool:
    '''
    Checks if previous printer is still reachable
    Args:
        cups.Connection,
        include_schemes: On wich schemes printes should be searched
    Returns:
        True if printer still there or False if not
    '''
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    connected_printers = conn.getPrinters()
    for v_cp in connected_printers.values():
        for k_ap in avilable_printers.keys():
            #print('{}: {}\n\n{}: {}'.format(k_ap,v_ap,k_cp,v_cp))
            if v_cp['device-uri'] == k_ap:
                return(True)
    return(False)

def check_avilable_printers(conn: cups.Connection, include_schemes: list = ['usb','driverless'], make_list: list = ['HP']) -> str:
    '''
    Checks if any printers are avilable and are on installation list

    Args:
        cups.Connection,
        include_schemes: On wich schemes printes should be searched
        make_list: list of printer manufacturers

    Returns printer-make if any prnters from make_list found or None
    '''
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    if len(avilable_printers) == 0:
        raise Exception('Printing: No printers found on scheme(s) {}'.format(include_schemes))
    #Check if any avilable printers on approuved list
    common_found = None
    l_avil = [v['device-make-and-model'].split(' ')[0] for v in avilable_printers.values()]
    for l1 in make_list:
        for l2 in l_avil:
            if l1 == l2:
                common_found = l1
                break
    if common_found is None:
        logging.error('Printing: No match. Printers found {}, allowed {}'.format(list(l_avil), list(make_list.keys())))
    return(common_found)

def install_printer(conn: cups.Connection,
                    printer_make:str = 'HP',
                    printer_driver:str = 'HP LaserJet Series PCL 6 CUPS',
                    include_schemes: list = ['usb','driverless'],
                    location = 'Local printer'
                    ) -> str:
    '''
    Installs kiosk printer, sets it as default, enabled

    Args:
        cups.Connection,
        printer_make: Printer's make,
        printer_driver: = CUPS driver to use for given make
        include_schemes: On wich schemes printes should be searched

    Returns printer name as in Cups or None
    '''
    full_name = None
    uri = None
    avilable_printers = conn.getDevices(include_schemes = include_schemes)
    if len(avilable_printers) == 0:
        raise Exception('Printing: No printers found on scheme(s) {}'.format(include_schemes))
    #Get data form device
    for k,v in avilable_printers.items():
        if v['device-make-and-model'].split(' ')[0].startswith(printer_make):
            name = v['device-make-and-model']
            full_name = name.replace(' ','_')
            uri = k
            break
    ppd_name = list(conn.getPPDs(ppd_make_and_model = list(printer_driver)[0]))[0]
    try:
        conn.addPrinter(name = full_name, ppdname = ppd_name, info = name, location = location, device = uri)
    except cups.IPPError as e:
        logging.error(e)
        return(None)
    else:
        conn.acceptJobs(full_name)
        conn.setPrinterShared(full_name,False)
        conn.setDefault(full_name)
        conn.enablePrinter(full_name)
        return(name)

def delete_all_printers(conn:cups.Connection):
    '''
    Deletetes all printers
    
    Args:
        cups.Connection

    Returns number od printer(s) deleted or None
    '''
    printers = conn.getPrinters()
    if len(printers) == 0:
        return(None)
    cnt = 0
    for p in printers:
        try:
            conn.deletePrinter(p)
        except cups.IPPError as e:
            logging.error(e)
        else:
            cnd =+ 1
    return(cnt)

def setup_printer(conn:cups.Connection, include_schemes=['usb','driverless'], driver_list:dict = None):
    '''
    Checks if cuurrently installed printer is avilable.
    If not, deletes all printers and installs new one if avilable and in driver_list.
    params conn: CUPS connection
    params include_schemes: CUPS schemes in which to search for avilable printers
    params driver_list: list of dics {printer_make: driver,...} (as in CUPS)
    '''
    if not current_printer_connected(conn, include_schemes):
        printer_make = None

        try:
            printer_make = check_avilable_printers(conn, include_schemes = include_schemes, make_list = driver_list.keys())
        except Exception as e:
            logging.error(e)
        else:
            delete_all_printers(conn)
            install_printer(conn, printer_make=printer_make, printer_driver = driver_list.values())

def main():
    conn = cups.Connection()
    config = {'include_schemes': ['usb'],
             'driver_list': {'Zebra':'Raw'}}
    setup_printer(conn=conn, include_schemes = config['include_schemes'], driver_list = config['driver_list'])
    print_queue = list(conn.getPrinters().keys())[0]
    print(print_queue)

if __name__ == '__main__':
    main()
