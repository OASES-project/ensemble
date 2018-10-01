#!/usr/bin/env python
"""When ecoinvent 3.5 was released, the file names have changed.
There has been some number added to the start of the filename,
but it can be ignored. This script takes the file_names from
#####_uuidAcitivity_uuidProduct to uuidAcitivity_uuidProduct

Warning: Currently does not do sensibility checks!
Use at you own responsibility! (and make a back up of you data!)
"""


import argparse
import os


def change_file_name(spoldfile_dir):

    print("Target directory is ", spoldfile_dir)
    user_choice = raw_input("Is this correct? y/n ")
    while user_choice not in ['y','n']:
        user_choice = raw_input("Invalid option, please choose again \n"\
                             "Is this correct? y/n ")
    if user_choice == 'n':
        var = raw_input("please provide the target correct target dir\n"\
                    "Or type q to quit! ")
        if var in ["q","Q"]:
            print("Quiting... Bye!")
            return
        else:
            spoldfile_dir = var
            
    print("saving current working directory")
    cwd = os.getcwd() #get cwd
    print("changing to target dir")
    os.chdir(spoldfile_dir)
    spoldfiles = os.listdir()
    
    for sfile in spoldfiles:
        #print(sfile)
        if len(sfile.split("_")) == 3:
            os.rename(file, "_".join(sfile.split("_")[1:]))
    
    print("file names changed")
    print("changeing back to working directory")
    os.chdir(cwd)#change back to originial wd
    print("Done!")
    return 


def ParseArgs():
    '''ParsArgs parser the command line options
    and returns them as a Namespace object
    '''
    print("Parsing arguments...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--dir", type=str, dest='target_dir',
                        default="/home/jakobs/data/ecoinvent/ei35_unlinked/datasets",
                        help="Directory containing the spoldfiles to be"\
                        "renamed")
    
    args = parser.parse_args()
    
    print("Arguments parsed.")
    return args


if __name__=="__main__":
    args = ParseArgs()
    change_file_name(args.target_dir)
