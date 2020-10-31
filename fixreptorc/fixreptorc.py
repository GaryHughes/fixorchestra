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

    # data types
    for source in repository.data_types.values():
        target = orc.DataType(source.name, source.base_type, source.added, source.description)
        orchestration.data_types[target.name] = target

    # code sets
    for source in repository.fields_by_tag.values():
        try:
            enum = repository.enums[source.id]
            codes = [orc.Code(value.id * 1000 + index, value.value, value.symbolic_name, value.added, value.description) for index, value in enumerate(enum, start=1)]
            target = orc.CodeSet(source.id, source.name, source.type, source.description, codes)
            orchestration.code_sets[target.name] = target
        except KeyError:
            pass

    # fields
    for source in repository.fields_by_tag.values():
        target = orc.Field(source.id, source.name, source.type, source.added, source.description)
        orchestration.fields_by_tag[target.id] = target
        orchestration.fields_by_name[target.name] = target

    # messages
    for source in repository.messages_by_msg_type.values():
        references = []
        # recursive search of repository.msg_contents starting wtih source.componentID
        
        target = orc.Message(source.componentID, source.name, source.msgType, source.categoryID, source.added, source.description, references)
        orchestration.messages_by_msg_type[target.msg_type] = target
        orchestration.messages_by_name[target.name] = target

    xml = orchestration.to_xml()

    ET.dump(indent(xml))
