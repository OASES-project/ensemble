# -*- coding: utf-8 -*-
"""
Created on Mon Okt 29 2018
@author: arthur jakobs

This script creates a concordance file for the geographical regions in
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

#%%





def BuildConcordance(ecoDir, exioDir, countryCodes, outDir):
    geoDict_ei = make_regiondict.GeoDict(ecoDir,returnDict=True)
    geoDf_ei = pd.DataFrame(data = np.array([list(geoDict_ei.keys()),
                          list(geoDict_ei.values())]).T, 
                          columns=['Code', 'Name'])
    del geoDict_ei
    regionFile_ex = os.path.join(exioDir,'EXIOBASE_CountryMapping_Master_20170320.csv')
    regionDf_ex = pd.read_csv(regionFile_ex, header=0, index_col=0)
    
    #split country-province codes e.g.: CN-.. to only contain country code e.g.: CN
    geoDf_ei = ParseCombiCodes(geoDf_ei)
    
    #merge eco and exio country list on iso codes
    countryConcord = geoDf_ei.merge(regionDf_ex, left_on='Code_2', right_on='ISO2', how='left', suffixes=('_eco', '_exio'))
    notMatched = countryConcord.loc[countryConcord['DESIRE code'].isnull()] #these are mostly the aggregate regions and some exceptions (i.e. XK)
    regionDict = BuildRegionDict(notMatched.Code.values)
    
        

    return

def GetDesireCode(ecoCode, countryConcord, regionDict):
    '''
    Input: ecoinvent region (code)
    Output: DESIRE (exiobase) code
    This function returns the DESIRE code (EXIO) from eco code input
    
    WARNING: Does not throw error when ecoCode does not have a valid exiobase mapping
    instead returns a None.
    '''
    if countryConcord.set_index('Code').loc[ecoCode,'DESIRE code'] is not np.NaN:
        desireCode = countryConcord.set_index('Code').loc[ecoCode,'DESIRE code']
    else:
        desireCode = regionDict[ecoCode]
    return desireCode


def BuildRegionDict(geo_codes):
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
                region_mapping[name] =  CountryList(name)
            except KeyError:
                region_mapping[name] = None
    return region_mapping


def CountryList(GEO):
    '''
    Input: ecoinvent region
    Return: list of country codes belonging to the 'region'

    Function returns a list of the country iso2 codes for the ecoinvent region
    in the input. Input is either a tuple ('ecoinvent', 'region') or just the
    just the 'region'. In the latter case the topology 'ecoinvent' is assumed.
    See documentation of constructive geometries at:
    https://github.com/cmutel/constructive_geometries
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
                        #This is an exception as the 'Québec, HQ distribution network' 
                        #only contains CA-QC which is an (econinvent, CA-QC) tuple.
            elif type(geo) == str and len(geo) == 2:
                #print('country')
                countries.append(geo)
            else: 
                print(geo)
    else:
        return None
    return countries


def FetchCountryListFromWiki():
    wiki_frames = pd.read_html('https://en.wikipedia.org/wiki/List_of_sovereign_states_and_dependent_territories_by_continent_(data_file)', 'Name', index_col=None, header=0)
    countries_by_continent = wiki_frames[1]
    #for some reason the continental code NA for North America is read as a NaN value. So Change it back
    countries_by_continent.loc[countries_by_continent.CC.isna(), 'CC'] = 'NA'
    return countries_by_continent

def ParseCombiCodes(df):
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


def Check_Output_dir(outPath):
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
    
    parser.add_argument("-E","--exiodir", type=str, dest='exio_dir', 
                        default="/home/jakobs/data/EXIOBASE/",
                        help="Directory containing the \n\
                        EXIOBASE_CountryMapping_Master_20170320.csv file,\n\
                        This is a csv version of the tab countries in the\n\
                        EXIOBASE_CountryMapping_Master_20170320.xlsx")
    
    parser.add_argument("-c", "--cc", type=str, dest="countryCodes",
                        default=None, help="path to file containing \n\
                        country iso-codes, continents. Otherwise take from:\n\
                        https://en.wikipedia.org/wiki/List_of_sovereign_states_and_dependent_territories_by_continent_(data_file)")
    
    parser.add_argument("-o","--outdir", type=str, dest='outdir', 
                        default=None,
                        help="Optional dir for output. Otherwise saved in \
                        subfolder in  input dir")
    


    args = parser.parse_args()
    
    print("Arguments parsed.")
    return args



if __name__ == "__main__":
    args = ParseArgs()    
    print("Running with the following arguments")
    for key, path in vars(args).items():
        print(key,': ', path)
    print("\n")
    BuildConcordance(*vars(args).values())
#%%
    

