#!/usr/bin/python3

import argparse
import os
import sys
sys.path.append("..")
from fixorchestra.orchestration import *
from fixrepository.repository import *

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--orchestration', required=True, help='The orchestration to load')
    parser.add_argument('--repository', required=True, help='A directory containing a repository to load e.g. fix_repository_2010_edition_20200402/FIX.4.4/Base')

    args = parser.parse_args()

    orchestration = Orchestration(args.orchestration)
    repository = Repository(args.repository)

    print("Fields Orchestration = {} Repository = {}".format(len(orchestration.fields), len(repository.fields)))
    print("Messages Orchestration = {} Repository = {}".format(len(orchestration.messages), len(repository.messages)))

    
