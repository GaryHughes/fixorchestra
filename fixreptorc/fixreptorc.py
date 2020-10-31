#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append("..")
import xml.etree.ElementTree as ET
import fixorchestra.orchestration as orc
import fixrepository.repository as rep

def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', required=True, metavar='directory', help='A directory containing a repository to load e.g. fix_repository_2010_edition_20200402/FIX.4.4/Base')

    args = parser.parse_args()

    repository = rep.Repository(args.repository)
    orchestration = orc.Orchestration()

    for source in repository.data_types.values():
        target = orc.DataType(source.name, source.base_type, source.added, source.description)
        orchestration.data_types[target.name] = target

    xml = orchestration.to_xml()

    ET.dump(indent(xml))
