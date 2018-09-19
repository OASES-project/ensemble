#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ensemble command line interface. See <insert website here> for more info.

Commands:

  * run: Run the ensemble model.
  * cleanup: Delete all model runs more than one week old.
  * xsd: Validate the ecospold2 files in <dirpath> against the default XSD or another XSD specified in <schema>.

Usage:
  # TODO: Adapt for ensemble
  ocelot-cli run <dirpath> [--noshow] [--save=<strategy>]
  ocelot-cli run <dirpath> <config> [--noshow] [--save=<strategy>]
  ocelot-cli cleanup
  ocelot-cli validate <dirpath>
  ocelot-cli xsd <dirpath> <schema>
  ocelot-cli xsd <dirpath>
  ocelot-cli -l | --list
  ocelot-cli -h | --help
  ocelot-cli --version

Options:
  --list             List the updates needed, but don't do anything
  --noshow           Don't open HTML report in new web browser tab
  --save=<strategy>  Strategy for which intermediate results to save.
  -h --help          Show this screen.
  --version          Show version.

"""
from docopt import docopt
import os
import sys


def main():
    try:
        args = docopt(__doc__, version='Ocelot open source linker CLI 0.2')
        if args['run']:
            system_model(args["<dirpath>"], args['<config>'], show=not args['--noshow'], save_strategy=args['--save'])
        elif args['validate']:
            validate_directory(args['<dirpath>'])
        elif args['xsd']:
            validate_directory_against_xsd(
              args['<dirpath>'],
              args['<schema>'] or os.path.join(data_dir, 'EcoSpold02.xsd')
            )
        elif args['cleanup']:
            cleanup_data_directory()
        else:
            raise ValueError
    except KeyboardInterrupt:
        print("Terminating Ocelot CLI")
        sys.exit(1)


if __name__ == "__main__":
    main()
