#!/usr/bin/env python3
import queue
import cups
import logging
from time import sleep
class kioPrinter(cups.Connection):
    def __init__(self,printers,testpage=True,connection=['usb']) -> None:
        super().__init__()
        self.printers=printers
        self.testpage = testpage
        self.uri=None
        self.connection = connection
        self.name=None
        self.running=False
    def start(self):
        '''
        If current default printer is set and avilable 'running' propery is set to True
        If current default printer N/A or not set - install if avilable
        '''
        avilablePrinters = self.getDevices(include_schemes=self.connection).keys()
        if len(avilablePrinters) == 0:
            logging.error('No printers detected on {}'.format(self.connection))
            return()
        #No default printer
        self.name=self.getDefault()
        if self.name is None:
            logging.info('No default printer')
            self.deleteAllPrinters()
            self.addKioPrinter()
            return()
        #Check if default printer is avilable
        self.uri = self.getPrinters()[self.name]['device-uri']
        if not (self.uri in avilablePrinters):
            logging.info('Default prnter not avilable')
            self.deleteAllPrinters()
            self.addKioPrinter()
            return()
        self.running=True
    def addKioPrinter(self):
        '''
        Adds printer in CUPS, sets it as default
        If success, sets 'running' True
        '''
        avilablePrinters = self.getDevices(include_schemes=self.connection)
        ppd_name=None
        printer_name=None
        for pal_key,pal_val in self.printers.items():
            for pav_key, pav_val in avilablePrinters.items():
                if avilablePrinters[pav_key]['device-make-and-model'].startswith(pal_key):
                    self.uri = pav_key
                    printer_name = pav_val['device-make-and-model']
                    self.name = ('{}_{}_'.format(printer_name,self.uri[-6:])).replace(' ','_')
                    ppd_name = list(self.getPPDs(limit=1, ppd_make_and_model=pal_val).keys())[0]
                    break
        if self.uri is None:
            logging.error('No {} printers detected on {}'.format(list(self.printers.keys()),self.connection).strip('['))
            return
        logging.info('Installing {}, PPD: {} on {}'.format(self.name,ppd_name,self.connection[0]))
        #Adding printer
        try:
            self.addPrinter(name=self.name, ppdname = ppd_name, info = printer_name, location = 'Local printer', device = self.uri)
            self.acceptJobs(self.name)
            self.setPrinterShared(self.name,False)
            self.setDefault(self.name)
            self.enablePrinter(self.name)
            if self.testpage:
                self.printTestPage(self.name)
            self.running=True
        except cups.IPPError as e:
            logging.error(e)
    def deleteAllPrinters(self):
        pl = self.getPrinters()
        if len(pl)>0:
            try:
                for p in pl:
                    self.deletePrinter(p)
                logging.info('{} printer(s) deleted'.format(len(pl)))
                return(True)
            except cups.IPPError as e:
                logging.info('deleteAllPrinters',e)
                return(False)
        return(None)
def main():
    logging.basicConfig(level=logging.DEBUG)
    plist={'Zebra':'Raw'}
    p=kioPrinter(plist,testpage=False)
    p.deleteAllPrinters()
    p.start()


    #p.printFile(printer=p.getDefault(),filename = '/home/pi/post.pdf',title = 'Report',options ={'print-color-mode': 'monochrome'})

if __name__=='__main__':
    main()
    