#!/usr/bin/python3

import argparse
import os
import sys
sys.path.append("..")
from fixorchestra.orchestration import *
from fixrepository.repository import *

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--orchestration', required=True, metavar='file', help='The orchestration to load')
    parser.add_argument('--repository', required=True, metavar='directory', help='A directory containing a repository to load e.g. fix_repository_2010_edition_20200402/FIX.4.4/Base')

    args = parser.parse_args()

    orchestration = Orchestration(args.orchestration)
    repository = Repository(args.repository)

    print("Fields Orchestration = {} Repository = {}".format(len(orchestration.fields_by_tag), len(repository.fields_by_tag)))
    
    field_errors = []
    for r_id, r_field in repository.fields_by_tag.items():
        try:
            o_field = orchestration.fields_by_tag[r_id]
            if o_field.name != r_field.name:
                field_errors.append("field Id = {} has Name = '{}' in the repository and Name = '{}' in the orchestration".format(r_id, r_field.name, o_field.name))
            if o_field.added != r_field.added:
                field_errors.append("field Id = {} has Added = '{}' in the repository and Added = '{}' in the orchestration".format(r_id, r_field.added, o_field.added))

            o_values = frozenset(orchestration.field_values(o_field))
            r_values = frozenset(repository.field_values(r_field))
            if len(o_values) != len(r_values):
                field_errors.append("field Name = {} has {} values in the repository and {} values in the orchestration".format(r_field.name, len(r_values), len(o_values)))
            o_extras = o_values - r_values
            r_extras = r_values - o_values
            if len(o_extras) > 0:
                print("field Name = {} has the following values in the orchestration not in the corresponding repostory field {}".format(r_field.name, [value.name for value in o_extras]))
            if len(r_extras) > 0:
                print("field Name = {} has the following values in rhe repository not in the corresponding orchestration field {}".format(r_field.name, [value.symbolic_name for value in r_extras]))
   
        except KeyError:
            print("orchestration does not contain a field with Id = {}".format(r_id))
    
    if len(field_errors) == 0:
        print("All fields have the same Name and Added values in the repository and the orchestration")
    else:
        print("The following {} discrepancies were found".format(len(field_errors)))
        for error in field_errors:
            print(error)

    print("Messages Orchestration = {} Repository = {}".format(len(orchestration.messages), len(repository.messages)))

    message_errors = []
    for msg_type, o_message in orchestration.messages_by_msg_type.items():
        r_message = repository.messages_by_msg_type[msg_type]
        if o_message.name != r_message.name:
            message_errors.append("message MsgType = {} has Name = '{}' in the repository and Name = '{}' in the orchestration".format(msg_type, r_message.name, o_message.name))
        if o_message.added != r_message.added:
            message_errors.append("message MsgType = {} has Added = '{}' in the repository and Added = '{}' in the orchestration".format(msg_type, r_message.added, o_message.added))
        o_fields = frozenset([field for field, indent in orchestration.message_fields(o_message)])
        r_fields = frozenset([field for field, indent in repository.message_fields(r_message)])
        if len(o_fields) != len(r_fields):
            message_errors.append("message MsgType = {} has {} fields in the repository and {} fields in the orchestration".format(msg_type, len(r_fields), len(o_fields)))
        o_extras = o_fields - r_fields
        r_extras = r_fields - o_fields
        if len(o_extras) > 0:
            message_errors.append("message MsgType = {} orchestration has the following fields not in the corresponding repository message {}".format(msg_type, [ field.name for field in o_extras]))    
        if len(r_extras) > 0:
            message_errors.append("message MsgType = {} repository has the following fields not in the corresponding orchestration message {}".format(msg_type, [ field.name for field in r_extras]))    
      
    if len(message_errors) == 0:
        print("All messages have the same Name values in the repository and the orchstration")
    else:
        print("The following {} discrepancies were found".format(len(message_errors)))
        for error in message_errors:
            print(error)
          



    if len(field_errors) > 0 or len(message_errors) > 0:
        sys.exit(-1)