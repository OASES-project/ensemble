"""
Created on Mon Nov 28 2018
@author: arthur jakobs
"""

#%%
import numpy as np
import os
import argparse
import sys
sys.path.append("../ecoparser/")
sys.path.append("../concordance")
from regions_concordance import RegionConcordance
from product_concordance import ProductConcordance
from regions_concordance import assert_list
sys.path.append("../utools")
import alogging
import pickle
import configparser
import gzip
import scipy.io as sio
#%%




def FillCuMatrix(config, logger):
    """
    Config is an object from the module configparser.
    Needs:
    A_exio          Exiobase A matrix

    exioProduct     The Exiobase product catagory, corresponding to the to be
                    hybridised ecoinvent process/product

    ecoPrice        The monetary price in ecoinvent for 1 unit of the product

    exioRegions     List of exiobase regions/countries for the ecoinvent process

    alphas          List of weight factors to determine the split over the
                    different exiobase regions. A process needing to be
                    hybridised over multiple regions needs to be split over
                    these regions based on the region's export share of the
                    product in the total export of the corresponding regions of
                    this product
    """
    #Declare function name for logging purpose
    _name = FillCuMatrix.__name__
    #READING IN DATA
    #ecoinvent prices
    logger.info(LogMessage(_name,'Reading ecoinvent price data...'))
    with open(config.get('eco_data','eco_flows'), 'rb') as fh:
        _,_,_,prices = pickle.load(fh)
    #ecoinvent matrices
    logger.info(LogMessage(_name,'Reading ecoinvent matrices...'))
    with gzip.open(config.get('eco_data','eco_matrices'), 'rb') as f:
        eco_obj = pickle.load(f)
    #EXIOBASE data
    logger.info(LogMessage(_name,'Reading EXIOBASE matrices...'))
    EB = sio.loadmat(config.get('exio_data','exio_matrices'))
    logger.info('Getting concordance')
    PC, RC = GetConcordance(config.get('concordance_data','productConcFile'),
                            config.get('concordance_data','productPickleFile'),
                            config.get('concordance_data','regionEcoDir'),
                            config.get('concordance_data','regionExioDir'),
                            config.get('concordance_data','regionPickleFile'),
                            config.get('concordance_data','concordance_outdir'),
                            logger)
    #create indices dictionary for products and regions
    ExProductDict = {}
    for i, prodCode in enumerate(EB['EB3_ProductCodes200']):
        ExProductDict[prodCode.rstrip()] = i
    ExCountryDict = {}
    for i, countryCode in enumerate(EB['EB3_RegionList']):
        ExCountryDict[countryCode] = i
    ExCountryDict['GLO'] = list(np.arange(len(EB['EB3_RegionList'])))
    Cu = np.empty((EB['EB3_A_ITC'].shape[0], eco_obj['A'].shape[0]))
    logger.info(LogMessage(_name,'Created empty Cu Matrix'))
    logger.info(LogMessage(_name,'Starting to fill the Cut off matrix...\n\
    ...this may take while...'))
    price_zero_counter = 0

    for i,ecoActPro in enumerate(eco_obj['A'].index.values):
        ecoProc, ecoProd = ecoActPro.split("_")
        exioProd, exioRegs, flag = Concordance(ecoProc, ecoProd, PC,
                                               RC, eco_obj['PRO'])
        if flag == 0 or flag == 1. or flag == 2:
            Cu[:,i] = np.zeros(Cu.shape[0])
        else:
            producer_indices, _, regions_indices, nProducts =\
                Code2Indices(exioProd, exioRegs, EB['EB3_ProductCodes200'],
                             EB['EB3_RegionList'], ExProductDict, ExCountryDict)
            alphas = CalculateAlphas(regions_indices, producer_indices,
                                     nProducts, EB['EB3_Z_ITC'])
            Cu[:,i], flag = CalcCu(producer_indices, alphas, prices, ecoProc,
                                   ecoProd, EB['EB3_A_ITC'])
            if flag == 0:
                price_zero_counter += 1
            else:
                exproducts2set0 = CorrectDoubleCountingBinary(
                                                     *ecoActPro.split('_'),
                                                     exioProd, PC, RC,
                                                     eco_obj['A'],
                                                     eco_obj['PRO'])
                if isinstance(exproducts2set0,np.ndarray):
                    row_indices, _, _, _ = Code2Indices(list(exproducts2set0),
                                                   'GLO',
                                                   EB['EB3_ProductCodes200'],
                                                   EB['EB3_RegionList'],
                                                   ExProductDict, ExCountryDict)
                    Cu[row_indices,i] = 0

    logger.info(LogMessage(_name,'Done filling Cu matrix'))

    Write2File(Cu, 'Cu_matrix', config.get('project_info', 'project_outdir'),
                                                                        logger)
    logger.info(LogMessage(_name,'Done'))


def Write2File(data, fileName, filePath, logger, fileType='pickle'):
    if fileType == 'pickle':
        full_path = os.path.join(filePath, fileName+'.pickle')
        logMessage = LogMessage(Write2File.__name__,
                                'Writing Cu Matrix to {}'.format(full_path))
        logger.info(logMessage)
        with open(full_path, 'wb') as fh:
            pickle.dump(data, fh)
        logger.info(LogMessage(Write2File.__name__,'Done!'))
    return


def LogMessage(name, message):
    """add the the (function-) name to the message"""
    new_message = '{} - {}'.format(name, message)
    return new_message


def GetConcordance(productConcFile, productPickleFile, regionEcoDir,
                   regionExioDir, regionPickleFile, concordanceOutDir, logger):
    PC = ProductConcordance(productConcFile, concordanceOutDir,
                            productPickleFile, saveConcordance=True,
                            logger=logger)
    PC.GetConcordance()
    logger.info(LogMessage(Concordance.__name__, 'Got product concordance'))
    RC = RegionConcordance(regionEcoDir, regionExioDir, concordanceOutDir,
                           regionPickleFile, saveConcordance=True,
                           logger=logger)
    RC.GetConcordance()
    logger.info(LogMessage(Concordance.__name__, 'Got region concordance'))
    return PC, RC


def Concordance(process, product, PC, RC, eco_pro):
    '''Input activityId, productId form ecoinvent.
       Returns exioProductCode, ExioRegionsList, flag.
       flag = 0: No product/process concordance
       flag = 1: No region concordance
       flag = 2: concordance found'''

    #first fo the product concordance. because if this does not work, there's
    #no need to do the region concordance.
    exioProduct = PC.GetExioProductCode(process, product)
    if exioProduct: #the above func returns None if it can't find a concordance
        ecoRegion, excluded = GetEcoRegion(process, product, eco_pro)
        if not ecoRegion:
            flag = 1
            return None, None, flag #Invalid ecoregion. Does not have a mapping
                                    #in exiobase
        else:
            #print('excluded:', excluded)
            exioRegionList = RC.GetDesireCode(ecoRegion, excluded=excluded)
            if exioRegionList == []:
                 flag = 2 #the exioRegionList is empty, all countries are
                          #exluded via their provinces
            else:
                flag = 3 #concordance found
        return exioProduct, exioRegionList, flag
    else:
        flag = 0 #No product/process concordance
        return None, None, flag


def GetEcoRegion(process, product, eco_pro):
    region = eco_pro.loc['_'.join((process, product)),'geography']
    activityNameId = eco_pro.loc['_'.join((process, product)),\
                                                        'activityNameId']
    #print('Eco Region: ',region)
    if region == 'RoW':
        all_regions = eco_pro.loc[np.logical_and(\
                         eco_pro['productId'] == product,\
                         eco_pro['activityNameId'] == activityNameId),\
                         'geography'].tolist()
        rowExcludedRegions = [x for x in all_regions if not x in ['RoW','GLO']]
        return region, rowExcludedRegions
    else:
        return region, None

def Code2Indices(product, regionlist, EB_ProductCodes200, EB_RegionList,
                 ExProductDict, ExCountryDict):
    if isinstance(product, list):
        prodInd = [ExProductDict[x] for x in product]
    else:
        prodInd = ExProductDict[product]
    regionlist = assert_list(regionlist)
    regionsInds = np.array([ExCountryDict[x] for x in regionlist])
    nProducts = len(ExProductDict)
    if isinstance(prodInd, list):
        exIndices = (np.array(prodInd).reshape(len(prodInd),1)+\
                              regionsInds*nProducts).flatten()
        exIndices.sort()
    else:
        exIndices = prodInd + regionsInds*nProducts
    return exIndices, prodInd, regionsInds, nProducts

def CalculateAlphas(regions_indices, producer_indices, nProducts, Z):
    '''For now this just uses share in total output of the producing regions
    to define the split over these different regions. Because of markets it is 
    not possible to trace down (or up-) stream supply chains.'''
    prodvol = Z[producer_indices,:].sum(axis=1)
    psum = prodvol.sum()
    if psum != 0:
        alphas = prodvol/psum
    else:
        alphas = np.ones(len(prodvol))
    return alphas


def GetPrice(actId, prodId, prices):
    '''Return the product price from the data frame prices.
    For now we assume basic (before tax) prices in Ecoinvent
    But this might change later.
    Secondly no price correction is currently applied. Needs to
    be corrected though, 2005 vs 2011!'''
    try:
        price = prices.loc['_'.join((actId, prodId)), 'amount']
    except KeyError:
        price = None
    return price


def CalcCu(producer_indices, alphas, prices, process, product, A_exio):
    '''Function '''
    price = GetPrice(process, product, prices)
    price_scaled = price/1e6 #convert EURO to MEURO EXIOBASE base 
    if price:
        Cu_column = np.sum(A_exio[:,producer_indices]*alphas,\
                                                                axis=1)*price
        return Cu_column, 1
    else:
        return np.zeros(A_exio.shape[0]), 0

def CorrectDoubleCountingBinary(proc, prod, exioProd, PC, RC, eco_A, eco_PRO):
    lcaInput = eco_A.index[eco_A['_'.join((proc,prod))] > 0]
    #print(eco_obj['PRO'].loc[lcaInput].activityName)
    excluded_products = []#list of products to explude from hybridisation
    for x in lcaInput:
        exioCat, _, _ = Concordance(*x.split('_'), PC, RC, eco_PRO)
        #print(exioProd, exioCat)
        if exioCat == exioProd:
            lcaInput_level2 = eco_A.index[eco_A[x] > 0]
            for x2 in lcaInput_level2:
                exioCat2, _, _ = Concordance(*x2.split('_'), PC, RC, eco_PRO)
                #print(exioCat2)
                if exioCat2 != exioProd:
                    #print('yes2')
                #else:
                    excluded_products.append(exioCat2)
        else:
            excluded_products.append(exioCat)

    excluded_products = [x for x in excluded_products if x is not None]
    if excluded_products:
        return np.unique(excluded_products)
    else:
        return None


def ParseArgs():
    '''
    ParsArgs parser the command line options
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()


    parser.add_argument("-c", "--config", type=str, dest='config_file',
                        default='./CuConfigFile.ini', help='path to the\
                        configuration file. Default file script folder.')

    parser.add_argument("--cc", dest="copy_config", action="store_true",
                        help="If True saves the config file to the log dir")

    parser.add_argument("--cs", dest="copy_script", action="store_true",
                        help="If True saves the script file to the log dir")

    args = parser.parse_args()

    print("Arguments parsed.")
    return args

if __name__ == "__main__":
    args = ParseArgs()
    #print("Running with the following arguments")
    #for key, path in vars(args).items():
    #    print(key,': ', path)
    #print("\n")
    if os.path.exists(args.config_file):
        print('Using configuration file: {}'.format(args.config_file))
        config = configparser.ConfigParser()
        config.read(args.config_file)
        print(config.sections())
        projectName = config.get('project_info', 'project_name')
        if config.get('project_info', 'log_dir'):
            log_dir = config.get('project_info', 'log_dir')
        else:
            log_dir = config.get('project_info', 'project_outdir')
        this_script_name = __file__
        logger = alogging.Logger(log_dir, projectName, this_script_name,
                                    args.copy_script, args.copy_config,
                                    os.path.realpath(args.config_file))

        FillCuMatrix(config,logger)

    else:
        print('Config file does not exist, please check path')
        print('exiting...')


