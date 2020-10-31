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
    
    field_errors = []
    for r_tag, r_field in repository.fields.items():
        try:
            # TODO - key orchestration.fields with an int as well
            o_field = orchestration.fields[str(r_tag)]
            if o_field.name != r_field.name:
                field_errors.append("field Id = {} has Name = '{}' in the repository and Name = '{}' in the orchestration".format(r_tag, r_field.name, o_field.name))
            if o_field.added != r_field.added:
                field_errors.append("field Id = {} has Added = '{}' in the repository and Added = '{}' in the orchestration".format(r_tag, r_field.added, o_field.added))
        except KeyError:
            print("orchestration does not contain a field with Id = {}".format(r_tag))
    
    if len(field_errors) == 0:
        print("All fields have the same Name and Added values in the repository and the orchestration")
    else:
        print("The following {} discrepancies were found".format(len(field_errors)))
        for error in field_errors:
            print(error)

    print("Messages Orchestration = {} Repository = {}".format(len(orchestration.messages), len(repository.messages)))

    message_errors = []
    for msg_type, o_message in orchestration.messages_by_msgtype.items():
        r_message = repository.messages_by_msg_type[msg_type]
        if o_message.name != r_message.name:
            message_errors.append("message MsgType = {} has Name = '{}' in the repository and Name = '{}' in the orchestration".format(msg_type, r_message.name, o_message.name))
        if o_message.added != r_message.added:
            message_errors.append("message MsgType = {} has Added = '{}' in the repository and Added = '{}' in the orchestration".format(msg_type, r_message.added, o_message.added))
        o_fields = orchestration.message_fields(o_message)
        r_fields = repository.message_fields(r_message)
        if len(o_fields) != len(r_fields):
            message_errors.append("message MsgType = {} has {} fields in the repository and {} fields in the orchestration".format(msg_type, len(r_fields), len(o_fields)))


    if len(message_errors) == 0:
        print("All messages have the same Name values in the repository and the orchstration")
    else:
        print("The following {} discrepancies were found".format(len(message_errors)))
        for error in message_errors:
            print(error)




    if len(field_errors) > 0 or len(message_errors) > 0:
        sys.exit(-1)