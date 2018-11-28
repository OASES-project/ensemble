-*- coding: utf-8 -*-
"""
Created on Mon Nov 26 2018
@author: arthur jakobs

This script creates an object of class ProductConcordance which returns a corresponding 
EXIOBASE prodcut for an entry of ecoinvent (activityId,productId)
The concordance is taken from the concordance matrix supplied by 
Maxime Agez @ CIRAIG Montreal.
"""

#%%
import numpy as np
import pandas as pd
import os
import datetime
import argparse
import pdb
import pickle
#%%



class ProductConcordance(object):
    '''
    Object Class that provides provides the functionality of looking up the
    corresponding exiobase product catagory to an ecoinvent
    (activityId, productID). It either needs an concordance excel file or can
    can read the concordance from a pickle file if run earlier.
    '''
    def __init__(self, concorFile, outDir, pickleFile=None,
                 saveConcordance=True):
        self.concorFile = concorFile
        self.outDir = outDir
        self.saveConcordance = saveConcordance
        self.pickleFile = pickleFile
        self.NotInConcordance = [] #a list of ecoinvent regions not present in
                                   #concordance. Currently also not being used
                                   #in ecoinvent 3.5

    def __repr__(self):
        return "Instance of class '{}'".format(self.__class__.__name__)


    def GetConcordance(self):
        if  self.pickleFile is not None and os.path.isfile(self.pickleFile):
            print('Reading in concordance from: {}'.format(self.pickleFile))
            with open(self.pickleFile,'rb') as fh:
                [self.productConcordance,
                 self.ActivityProductConcordance] = pickle.load(fh)
        elif self.pickleFile is not None:
            print('Pickle file given does not exist.')
            self.ReadConcordanceFromExcel()
        else:
            self.ReadConcordanceFromExcel()
        return


    def ReadConcordanceFromExcel(self):
        '''
        '''
        print('Reading in concordance from Excelfile...')
        self.productConcordance = pd.read_excel(self.concorFile,
                                         sheet_name='Concordance per product',
                                         index_col=0)
        self.ActivityProductConcordance =  pd.read_excel(self.concorFile,
                                         sheet_name='Exceptions',
                                         index_col=0)
        if self.saveConcordance:
            self.SaveConcordance()

        return

    def GetExioProductCode(self, activityId, productId):
        '''
        Input: ecoinvent activityId, productId
        Output: exiobase productId
        '''
        act_prod = '_'.join((activityId, productId))
        print(act_prod)
        if act_prod  in self.ActivityProductConcordance.index.values:
            exioProductCode = self.ActivityProductConcordance.loc[act_prod,
                                                            'Concordance_1']
        elif productId in self.productConcordance.index.values:
            exioProductCode = self.productConcordance.loc[productId,
                                                            'Concordance_2']
        else:
            exioProductCode = None
        return exioProductCode
    
    @staticmethod
    def Check_Output_dir(outPath):
        if not os.path.exists(outPath):
            os.makedirs(outPath)
            print("Created directory {}".format(outPath))
        return

    def SaveConcordance(self):
        print('Saving concordance...')
        self.Check_Output_dir(self.outDir)
        outFile = os.path.join(self.outDir,
                               'EcoExioProductConcordance_{}.pickle'.format(
                               datetime.datetime.date(datetime.datetime.now())))
        
        saveList = [self.productConcordance, self.ActivityProductConcordance]
        
        with open(outFile, 'wb') as fh:
            pickle.dump(saveList, fh)
        print('Concordance saved to: {}'.format(outFile))
        return

def assert_list(something):
    if not isinstance(something, list):
        return [something]
    return something
    
def ParseArgs():
    '''
    ParsArgs parser the command line options
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--dir", type=str, dest='concordance_file',
                        default='/home/jakobs/data/EcoBase/Product_Concordances-ei35-exio.xlsx',
                        help="The concordance excel file")
    
    parser.add_argument("-o","--outdir", type=str, dest='outdir',
                        default='/home/jakobs/data/EcoBase/',
                        help="Optional dir for output. Otherwise saved in \
                        subfolder in  input dir")
    
    parser.add_argument("-f","--picklefile", type=str, dest='picklefile',
                        default=None, help="Concordance pickle file to load\
                        from.")
    
    parser.add_argument("-s","--save", dest='saveconcord', action='store_true',
                        help="If True saves output as pickle file too")
    
    args = parser.parse_args()
    
    print("Arguments parsed.")
    return args

if __name__ == "__main__":
    args = ParseArgs()
    print("Running with the following arguments")
    for key, path in vars(args).items():
        print(key,': ', path)
    print("\n")
    PC = ProductConcordance(*vars(args).values())
    PC.GetConcordance()
    exiocode = PC.GetExioProductCode('6885fd40-ff73-40a4-8f71-225577ec684e',
                                     'aeaf5266-3f9c-4074-bd34-eba76a61760c')
    print(exiocode)
