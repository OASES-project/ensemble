#! /bin/usr/env pytho
'''
author: Arthur Jakobs
Okt 25 2018

Simple function/script to parse the ecoinvent regions
into a dictionary of the form {abbreviantion: region name}
and saves it in json file
'''

from lxml import objectify
import os
import json
import pickle
import argparse
import sys


def GeoDict(eco_dir, outfile=None, outdir=None, Pickle=False, returnDict=False):
    '''
    GeoDict is a function that parses the ecoinvent
    Geographies.xml file into a dictionary and saves
    that into a json file and optionally a pickle file.
    
    Usage:
    'eco_dir':          "Directory containing the ecoinvent meta data,\n\
                        i.e. the ecoinvent MasterData folder."
    
    'outfile':          "Optional filename for output. Otherwise saved as Geographies.json")

    'outdir':           "Optional dir for output. Otherwise saved in  input dir")
    
    'pickle':           "If True saves output as pickle file too")
    
    'returnDict':       "If True, main function returns dictionary")
                        #for later use as function

    '''
    geoNames = []
    geoAbbrevs = []
    root = objectify.parse(os.path.join(eco_dir, 'Geographies.xml')).getroot()
    for child in root.getchildren():
        if hasattr(child, 'name'):
            geoNames.append(str(child.name))
            geoAbbrevs.append(str(child.shortname)) 
    geoDict = {key:value for (key, value) in zip(geoAbbrevs, geoNames)}
    if returnDict == True:
        return geoDict
    else:
        Write2File(outfile, outdir, eco_dir, Pickle, geoDict)
        return



def Write2File(outfile, outdir, eco_dir, Pickle, geoDict):
    outPath = Check_Output_dir(outdir, eco_dir)
    fileName = FileName(outfile)
    fileString = os.path.join(outPath,fileName)
    with open(fileString, 'w') as fh:
        json.dump(geoDict, fh)
    print('dictionary written to:\n{}'.format(fileString))
    if Pickle:
        pickleName = os.path.splitext(fileName)[0]+'.pickle'
        fileString = os.path.join(outPath, pickleName)
        with open(fileString, 'wb') as fh:
            pickle.dump(geoDict, fh)
        print('dictionary written to:\n{}'.format(fileString))
    return

def FileName(outfile):
    '''
    Returns a file name given as argument,
    otherwise the default name.
    '''
    if outfile:
        filename = outfile
    else:
        filename = 'Geographies.json'
    return filename

def Check_Output_dir(outdir, eco_dir):
    '''
    Returns a output dir and
    creates it if it does not exist
    '''
    if outdir:
        outPath = outdir
    else:
        outPath = eco_dir
    if not os.path.exists(outPath):
        os.makedirs(outPath)
        print("Created directory {}".format(outPath))
    return outPath

def ParseArgs():
    '''
    ParsArgs parser the command line options 
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--dir", type=str, dest='eco_dir', 
                        default='/home/jakobs/data/ecoinvent/ecoinvent 3.5_cutoff_ecoSpold02/ecoinvent 3.5_cutoff_ecoSpold02/MasterData',
                        help="Directory containing the ecoinvent meta data,\n\
                        i.e. the ecoinvent MasterData folder.")
    
    parser.add_argument("-f","--outfile", type=str, dest='outfile', 
                        default=None,
                        help="Optional filename for output. Otherwise saved as Geographies.json")

    parser.add_argument("-o","--outdir", type=str, dest='outdir', 
                        default=None,
                        help="Optional dir for output. Otherwise saved in  input dir")
    
    parser.add_argument("-p","--pickle", dest='Pickle',
                        action='store_true',
                        help="If True saves output as pickle file too")
    
    parser.add_argument("-r","--returndict", dest='returnDict',
                        action='store_true',
                        help="If True, main function returns dictionary")
                        #for later use as function

    args = parser.parse_args()
    
    print("Arguments parsed.")
    return args



if __name__ == "__main__":
    args = ParseArgs()    
    print('Running with following arguments:')
    for key, path in vars(args).items():
        print(key,': ', path)    
    GeoDict(*vars(args).values())

    
