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

#%%

def BuildConcordance(ecoDir, exioDir, countryCodes, outDir):
    geoDict_ei = make_regiondict.GeoDict(ecoDir,returnDict=True)
    geoDf_ei = pd.DataFrame(data = np.array([list(geoDict_ei.keys()),
                          list(geoDict_ei.values())]).T, 
                          columns=['Code', 'Name'])
    del geoDict_ei
    regionFile_ex = os.path.join(exioDir,'countries.csv')
    regionDf_ex = pd.read_csv(regionFile_ex, header=0, index_col=0)

    geoDf_ei = ParseCombiCodes(geoDf_ei)
    #now get a table of countries bby continent:
    if countryCodes:
        print("in the future need to read country codes from file: {}".formtat(
              countryCodes))
    else:
        countries_by_continent = FetchCountryListFromWiki()
    #Now merge DataFrames in two steps:
    step_1 = geoDf_ei.join(countries_by_continent.set_index('a-2'), on='Code_2', lsuffix='_eco', rsuffix='_cc')
    step_2 = step_1.merge(regionDf_ex, how='left', left_on='Code_2', right_on='DESIRE code')
    step_2['flag'] = [np.NaN for i in range(len(step_2))] #add a flag column for later use

    return


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
                        help="Directory containing the countries.csv file,\n\
                        This is a csv version of the tab countries in the\n\
                        supplementary material 9 from Stadler et al. 2018\n\
                        DOI: 10.1111/jiec.12715")
    
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
    

