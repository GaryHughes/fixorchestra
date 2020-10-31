#!/usr/bin/python3

import argparse
import xml.etree.ElementTree as ET
import os

class DataType:

    def __init__(self, name, base_type, description, added):
        self.name = name
        self.base_type = base_type
        self.description = description
        self.added = added

class Enum:

    def __init__(self, tag, value, symbolicName, description, added):
        self.tag = tag
        self.value = value
        self.symbolicName = symbolicName
        self.description = description
        self.added = added

class Field:

    def __init__(self, tag, name, type, description, added):
        self.tag = tag
        self.name = name
        self.type = type
        self.description = description
        self.added = added

class Component:

    def __init__(self, componentID, componentType, categoryID, name, description, added):
        self.componentID = componentID
        self.componentType = componentType
        self.categoryId = categoryID
        self.name = name
        self.description = description
        self.added = added


class MsgContent:

    def __init__(self, componentID, tagText, indent, position, reqd, description, added):
        self.componentID = componentID
        self.tagText = tagText
        self.indent = indent
        self.position = position
        self.reqd = reqd
        self.description = description
        self.added = added


class Message:

    def __init__(self, componentID, msgType, name, categoryID, sectionID, description, added):
        self.componentID = componentID
        self.msgType = msgType
        self.name = name
        self.categoryID = categoryID
        self.sectionID = sectionID
        self.description = description
        self.added = added


class Repository:

    enums = {}          # Enum.tag -> [Enum]
    fields = {}         # Field.tag -> Field
    data_types = {}     # DataType.name -> DataType
    components = {}     # Component.componentID -> Component
    msg_contents = {}   # MsgContent.componentID -> [MsgContent]
    messages = []       # [Message]
    messages_by_msg_type = {} # Message.msg_type -> Message

    def __init__(self, directory):
        if not os.path.exists(directory):
            raise Exception("directory '{}' does not exist".format(directory))
        self.load_abbreviations(directory)
        self.load_categories(directory)
        self.load_components(directory)
        self.load_data_types(directory)
        self.load_enums(directory)
        self.load_fields(directory)
        self.load_messages(directory)
        self.load_msg_contents(directory)
        self.load_sections(directory)
      
    def load_components(self, directory):
        # <Component added="FIX.4.0">
        #     <ComponentID>1002</ComponentID>
        #     <ComponentType>Block</ComponentType>
        #     <CategoryID>Session</CategoryID>
        #     <Name>StandardTrailer</Name>
        #     <NotReqXML>1</NotReqXML>		
        #     <Description>The standard FIX message trailer</Description>
	    # </Component>
        filename = os.path.join(directory, 'Components.xml')
        if not os.path.exists(filename):
            raise Exception("directory '{}' does not contain a Components.xml".format(directory))
        componentsElement = ET.parse(filename).getroot()
        for componentElement in componentsElement.findall('Component'):
            component = Component(
                componentElement.find('ComponentID').text,
                componentElement.find('ComponentType').text,
                componentElement.find('CategoryID').text,
                componentElement.find('Name').text,
                componentElement.find('Description').text,
                componentElement.get('added')
            )
            self.components[component.componentID] = component

  
    def load_data_types(self, directory):
        # <Datatype added="FIX.4.2">
        #     <Name>Qty</Name>
        #     <BaseType>float</BaseType>
        #     <Description>float field (see definition of "float" above) capable of storing either a whole number (no decimal places) of "shares" or a decimal value containing decimal places for non-share quantity asset classes.</Description>
        # </Datatype>
        filename = os.path.join(directory, 'Datatypes.xml')
        if not os.path.exists(filename):
            raise Exception("directory '{}' does not contain a Datatypes.xml".format(directory))
        dataTypesElement = ET.parse(filename).getroot()
        for dataTypeElement in dataTypesElement.findall('Datatype'):
            baseType = dataTypeElement.find('BaseType')
            dataType = DataType(
                dataTypeElement.find('Name').text,
                baseType.text if baseType is not None else None,
                dataTypeElement.find('Description').text,
                dataTypeElement.get('added')
            )
            self.data_types[dataType.name] = dataType


    def load_enums(self, directory):
        # <Enum added="FIX.2.7">
        #     <Tag>4</Tag>
        #     <Value>S</Value>
        #     <SymbolicName>Sell</SymbolicName>
        #     <Description>Sell</Description>
    	# </Enum>
        filename = os.path.join(directory, 'Enums.xml')
        if not os.path.exists(filename):
            raise Exception("directory '{}' does not contain an Enums.xml".format(directory))
        enumsElement = ET.parse(filename).getroot()
        for enumElement in enumsElement.findall('Enum'):
            enum = Enum(
                enumElement.find('Tag').text,
                enumElement.find('Value').text,
                enumElement.find('SymbolicName').text,
                enumElement.find('Description').text,
                enumElement.get('added')
            )
            try:
                self.enums[enum.tag].append(enum)
            except KeyError:
                self.enums[enum.tag] = [enum]
        

    def load_fields(self, directory):
        # <Field added="FIX.2.7">
        #     <Tag>4</Tag>
        #     <Name>AdvSide</Name>
        #     <Type>char</Type>
        #     <NotReqXML>1</NotReqXML>
        #     <Description>Broker's side of advertised trade</Description>
        # </Field>
        filename = os.path.join(directory, 'Fields.xml')
        if not os.path.exists(filename):
            raise Exception("directory '{}' does not contain a Fields.xml".format(directory))
        fieldsElement = ET.parse(filename).getroot()
        for fieldElement in fieldsElement.findall('Field'):
            field = Field(
                fieldElement.find('Tag').text,
                fieldElement.find('Name').text,
                fieldElement.find('Type').text,
                fieldElement.find('Description').text,
                fieldElement.get('added')
            )
            self.fields[field.tag] = field


    def load_messages(self, directory):
        # <Message added="FIX.2.7">
        #     <ComponentID>2</ComponentID>
        #     <MsgType>1</MsgType>
        #     <Name>TestRequest</Name>
        #     <CategoryID>Session</CategoryID>
        #     <SectionID>Session</SectionID>
        #     <NotReqXML>1</NotReqXML>
        #     <Description>The test request message forces a heartbeat from the opposing application.</Description>
        # </Message>
        filename = "Messages.xml"
        path = os.path.join(directory, filename)
        if not os.path.exists(path):
            raise Exception("directory '{}' does not contain a {}".format(directory, filename))
        for messageElement in ET.parse(path).getroot().findall('Message'):
            message = Message(
                messageElement.find('ComponentID').text,
                messageElement.find('MsgType').text,
                messageElement.find('Name').text,
                messageElement.find('CategoryID').text,
                messageElement.find('SectionID').text,
                messageElement.find('Description').text,
                messageElement.get('added')
            )
            self.messages.append(message)
            self.messages_by_msg_type[message.msgType] = message
      

    def load_msg_contents(self, directory):
        # <MsgContent added="FIX.2.7">
        #     <ComponentID>1</ComponentID>
        #     <TagText>StandardHeader</TagText>
        #     <Indent>0</Indent>
        #     <Position>1</Position>
        #     <Reqd>1</Reqd>
        #     <Description>MsgType = 0</Description>
        # </MsgContent>
        filename = os.path.join(directory, 'MsgContents.xml')
        if not os.path.exists(filename):
            raise Exception("directory '{}' does not contain a MsgContents.xml".format(directory))
        msgContentsElement = ET.parse(filename).getroot()
        for msgContentElement in msgContentsElement.findall('MsgContent'):
            description = msgContentElement.find('Description')
            msgContent = MsgContent(
                msgContentElement.find('ComponentID').text,
                msgContentElement.find('TagText').text,
                msgContentElement.find('Indent').text,
                msgContentElement.find('Position').text,
                msgContentElement.find('Reqd').text,
                description.text if description is not None else None,
                msgContentElement.get('added')
            )
            try:
                self.msg_contents[msgContent.componentID].append(msgContent)
            except KeyError:
                self.msg_contents[msgContent.componentID] = [msgContent]


    def load_sections(self, directory):
        pass

    def load_abbreviations(self, directory):
        pass

    def load_categories(self, directory):
        pass


def dump_field(repository, tag):
    field = repository.fields[tag]
    print(field.name + " {")
    print("    Tag   = " + field.tag)
    print("    Type  = " + field.type)
    print("    Added = " + field.added)
    print("    (" + field.description + ")")
    try:
        enums = repository.enums[field.tag]
        print("    Values {")
        for enum in enums:
            print("        {} ({}, {}, {})".format(enum.value, enum.symbolicName, enum.added, enum.description))
        print("    }")
    except KeyError:
        pass
    print("}")


def dump_msg_contents(repository):
    pass


def dump_message(repository, msg_type):
    message = repository.messages_by_msg_type[msg_type]
    print(message.name + " {")
    print("    ComponentId = " + message.componentID)
    print("    MsgType = " + message.msgType)
    print("    CategoryID = " + message.categoryID)
    print("    SectionID = " + message.sectionID)
    print("    Added = " + message.added)
    print("    (" + message.description + ")")
    print("    MsgContents {")
    #dump_msg_contents(repository, message.references, 2)
    print("    }")
    print("}")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', required=True, help='A directory containing a repository to load e.g. fix_repository_2010_edition_20200402/FIX.4.4/Base')
    parser.add_argument('--dump_field', required=False, help='Display the content of a message')
    parser.add_argument('--dump_message', required=False, help='Display the content of a message')
  
    args = parser.parse_args()

    repository = Repository(args.repository)

    if args.dump_field:
        dump_field(repository, args.dump_field)

    if args.dump_message:
        dump_message(repository, args.dump_message)

