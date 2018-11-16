# -*- coding: utf-8 -*-
"""
Created on Mon Okt 29 2018
@author: arthur jakobs

This script containsa functions to return condordance of products in
in ecoinvent and exiobase. 
"""

#%%
import numpy as np
import scipy.io
import scipy
import pandas as pd
import os
import datetime
import argparse
import pdb
import sys
sys.path.append("../ecoparser/")
import make_regiondict
import constructive_geometries as cg
import pickle
#%%



class ProductConcordance(object):
    '''
    Object Class that builds the relevant concordance dataframes and
    dictionaries. Main function after initinalisation via BuildConcordance is
    GetDesireCode(ecoCode), which returns the DESIRE/EXIOBASE region code given
    the ecoinvent region code (ecoCode).
    
    Needs 
    '''
    def __init__(self, ecoDir, exioDir, outDir, pickleFile=None,
                 saveConcordance=True):
        self.ecoDir = ecoDir
        self.exioDir = exioDir
        self.outDir = outDir
        self.saveConcordance = saveConcordance
        self.pickleFile = pickleFile

    def __repr__(self):
        return "Instance of class '{}'".format(self.__class__.__name__)


    def GetConcordance(self):
        if  self.pickleFile is not None and os.path.isfile(self.pickleFile):
            print('Reading in concordance from: {}'.format(self.pickleFile))
            with open(self.pickleFile,'rb') as fh:
                [self.countryConcord,
                 self.notMatched,
                 self.regionDict] = pickle.load(fh)
        elif self.pickleFile is not None:
            print('Pickle file given does not exist.')
            self.BuildConcordance()
        else:
            self.BuildConcordance()
        return


    def BuildConcordance(self):
        '''
        This function builds the necessary DataFrames and Dictionaries:
       
        self.countryConcord :       Main concordance DataFrame
        self.notMatched = c :       DataFrame containing the regions that
                                    did not match on their iso code
        self.regionDict = B :
        '''
        print('Building concordance...')
        geoDict_ei = make_regiondict.GeoDict(self.ecoDir,returnDict=True)
        geoDf_ei = pd.DataFrame(data = np.array([list(geoDict_ei.keys()),
                              list(geoDict_ei.values())]).T, 
                              columns=['Code', 'Name'])
        regionFile_ex = os.path.join(self.exioDir,
                         'EXIOBASE_CountryMapping_Master_20170320.csv')
        regionDf_ex = pd.read_csv(regionFile_ex, header=0, index_col=0)
        
        #split country-province codes e.g.: CN-..
        #to only contain country code e.g.: CN
        geoDf_ei = self.ParseCombiCodes(geoDf_ei)
        
        #merge eco and exio country list on iso codes
        self.countryConcord = geoDf_ei.merge(regionDf_ex, left_on='Code_2',
                                             right_on='ISO2', how='left',
                                             suffixes=('_eco', '_exio'))
        
        not_matched_mask = self.countryConcord['DESIRE code'].isnull()
        self.notMatched = self.countryConcord.loc[not_matched_mask] 
        #these are mostly the aggregate regions and some exceptions (i.e. XK)
        self.BuildRegionDict(self.notMatched.Code.values)
        
        if self.saveConcordance:
            self.SaveConcordance()

        return


    def GetDesireCode(self, ecoCode):
        '''
        Input: ecoinvent region (code)
        Output: DESIRE (exiobase) code
        This function returns the DESIRE code (EXIO) from eco code input
        
        WARNING: Does not throw error when ecoCode does not have a valid
        exiobase mapping instead returns a None.
        '''
        value = self.countryConcord.set_index('Code').loc[ecoCode,'DESIRE code']
        if not np.isnan(value):
            print('Region in main concordance')
            desireCode = value
        else:
            print('Looking up region via region regiondict')
            desireCode = self.regionDict[ecoCode]
        
        return desireCode
    
    
    def BuildRegionDict(self, geo_codes):
        '''
        Input: list of ecoinvent regions (ones that are not matched on a 
                                             country basis)
        Return: dictionary{region: list of countries in region}
    
        Builds a regionDict where regionDict['region'] returns a
        list of the country codes that belong to the region. 
        There are a few regions that do not contain countries or are not
        present in constructive geometries, those will get a None as return.
        '''
        region_mapping = {}
        for name in geo_codes:
        #GLOBAL and RoW need to be handled differently
            if name not in ['RoW', 'GLO']:    
                try: 
                    region_mapping[name] =  self.CountryList(name)
                except KeyError:
                    region_mapping[name] = None
        
        self.regionDict = region_mapping
        
        return 


    def CountryList(self, GEO):
        '''
        Input: ecoinvent region
        Return: list of country codes belonging to the 'region'
    
        Function returns a list of the country iso2 codes for the ecoinvent
        region in the input. Input is either a tuple ('ecoinvent', 'region')
        or just the just the 'region'. In the latter case the topology
        'ecoinvent' is assumed. See documentation of constructive geometries
        at: https://github.com/cmutel/constructive_geometries
        '''
        geomatcher = cg.Geomatcher()
        if not geomatcher.contained(GEO, include_self=False) == []:
            countries = []
            for geo in geomatcher.contained(GEO, include_self=False):
                #print(geo, ': ', geomatcher.contained(geo, include_self=False))
                if type(geo)==tuple:
                    #print(tuple)
                    for subgeo in geomatcher.contained(geo, include_self=False):
                        if subgeo not in geomatcher.contained(GEO):
                            countries.append(subgeo)
                        elif geo[1] == 'CA-QC' and 'CA' not in countries:
                            countries.append('CA')
                            #This is an exception as the 
                            #'Québec, HQ distribution network' only contains
                            #CA-QC which is an (econinvent, CA-QC) tuple.
                elif type(geo) == str and len(geo) == 2:
                    #print('country')
                    countries.append(geo)
                else: 
                    print(geo)
        else:
            return None
        return countries


    def ParseCombiCodes(self, df):
        '''Splits the code names with a -
        into single 2 letter codes. I.e.
        get rid of province level detail'''
        #first split codes at -
        df['Code_2'] = df['Code'].str.split('-')
        #Then handle case individually
        for i in range(len(df['Code_2'].values)):
            if len(df.Code_2.iloc[i]) > 1:
                if df.Code_2.iloc[i][0] == 'UN':
                    #if one of the #UN regions, only save the region part of it
                    df.Code_2.iloc[i] = df.Code_2.iloc[i][1]
                elif df.Code_2.iloc[i][0] == 'AUS':
                    df.Code_2.iloc[i] = 'AU'
                else:
                    df.Code_2.iloc[i] = df.Code_2.iloc[i][0]
            else:
                df.Code_2.iloc[i] = df.Code_2.iloc[i][0]
        return df
    
    
    def Check_Output_dir(self, outPath):
        if not os.path.exists(outPath):
            os.makedirs(outPath)
            print("Created directory {}".format(outPath))
        return outPath
    

    def SaveConcordance(self):
        print('Saving concordance...')
        outPath = self.Check_Output_dir(self.outDir)
        outFile = os.path.join(self.outDir,
                               'EcoExioRegionConcordance_{}.pickle'.format(
                               datetime.datetime.date(datetime.datetime.now())))
        
        saveList = [self.countryConcord, self.notMatched, self.regionDict]
        
        with open(outFile, 'wb') as fh:
            pickle.dump(saveList, fh)
        print('Concordance saved to: {}'.format(outFile))
        return


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
    
    parser.add_argument("-E","--exiodir", type=str, dest='exio_dir', 
                        default="/home/jakobs/data/EXIOBASE/",
                        help="Directory containing the \n\
                        EXIOBASE_CountryMapping_Master_20170320.csv file,\n\
                        This is a csv version of the tab countries in the\n\
                        EXIOBASE_CountryMapping_Master_20170320.xlsx")
    
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
    CC = RegionConcordance(*vars(args).values())
    CC.GetConcordance()
    print(CC.GetDesireCode('UN-EASIA'))
    pdb.set_trace()

