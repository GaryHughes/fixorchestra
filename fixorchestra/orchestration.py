#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import datetime

xs_namespace = 'http://www.w3.org/2001/XMLSchema'
functx_namespace = 'http://www.functx.com'
fixr_namespace = 'http://fixprotocol.io/2020/orchestra/repository'
dc_namespace = 'http://purl.org/dc/elements/1.1/'
xsi_namespace = 'http://www.w3.org/2001/XMLSchema-instance'

namespaces = { 
    'xs'     : xs_namespace,
    'functx' : functx_namespace,
    'fixr'   : fixr_namespace,
    'dc'     : dc_namespace, 
    'xsi'    : xsi_namespace 
}

class DataType:

    def __init__(self, name, base_type, added, synopsis):
        self.name = name
        self.base_type = base_type
        self.added = added
        self.synopsis = synopsis


class Code:
    # This class needs to be kept in sync with repository.Enum because fixaudit.py stores 
    # instances of these classes in Sets. Specifically both implementations have to be hashable 
    # and they have to be hashing the same thing.
    def __init__(self, id, name, value, added, synopsis):
        self.id = id
        self.name = name
        self.value = value
        self.added = added
        self.synopsis = synopsis

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, rhs):
        return self.value == rhs.value


class CodeSet:
 
    def __init__(self, id, name, type, synopsis, codes):
        self.id = id
        self.name = name
        self.type = type
        self.synopsis = synopsis
        self.codes = codes

class Field:
    # This class needs to be kept in sync with repository.Field because fixaudit.py stores 
    # nstances of these classes in Sets. Specifically both implementations have to be hashable 
    # and they have to be hashing the same thing.
    def __init__(self, id, name, type, added, synopsis):
        self.id = id
        self.name = name
        self.type = type
        self.added = added
        self.synopsis = synopsis

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, rhs):
        return self.id == rhs.id


class Reference:

    def __init__(self, field_id, group_id, component_id, presence, added, synopsis):
        #if field_id and group_id:
        #    raise Exception('A Reference cannot have both a field_id and a group_id')
        self.field_id = field_id
        self.group_id = group_id
        self.component_id = component_id
        self.presence = presence
        self.added = added
        self.synopsis = synopsis

class Component:

    def __init__(self, id, name, category, added, synopsis, references):
        self.id = id
        self.name = name
        self.category = category
        self.added = added
        self.synopsis = synopsis
        self.references = references

class Group:

    def __init__(self, id, name, added, category, synopsis, references):
        self.id = id
        self.name = name
        self.added = added
        self.category = category
        self.synopsis = synopsis
        self.references = references

class Message:

    def __init__(self, id, name, msg_type, category, added, synopsis, references):
        self.id = id
        self.name = name
        self.msg_type = msg_type
        self.category = category
        self.added = added
        self.synopsis = synopsis
        self.references = references
 
       
class Orchestration:

    data_types = {}             # DataType.name -> DataType
    code_sets = {}              # CodeSet.name -> CodeSet
    fields_by_tag = {}          # Field.id -> Field
    fields_by_name = {}         # Field.name.lower() -> Field
    components = {}             # Componnet.id -> Component
    groups = {}                 # Group.id -> Group
    messages = {}               # Message.id -> Message
    messages_by_msg_type = {}   # Message.msg_type -> Message
    messages_by_name = {}       # Message.name.lower() -> Message

    def __init__(self, filename = None):
        if filename == None:
            return
        self.filename = filename
        tree = ET.parse(filename)
        repository = tree.getroot()
        self.load_data_types(repository)
        self.load_code_sets(repository)
        self.load_fields(repository)
        self.load_components(repository)
        self.load_groups(repository)
        self.load_messages(repository)

    def references_to_fields(self, references, depth):
        result = []
        for reference in references:
            if reference.field_id:
                result.append((self.fields_by_tag[reference.field_id], depth))
            elif reference.group_id:
                group = self.groups[reference.group_id]
                result = result + self.references_to_fields(group.references, depth + 1)
            elif reference.component_id:
                component = self.components[reference.component_id]
                result = result + self.references_to_fields(component.references, depth)
        return result


    def message_fields(self, message):
        return self.references_to_fields(message.references, 0)


    def field_values(self, field):
        try:
            return self.code_sets[field.type].codes
        except KeyError:
            return []


    def extract_synopsis(self, element):
        # <element>
        #   <fixr:annotation>
        #       <fixr:documentation purpose="SYNOPSIS">
        #           int field representing the number of entries in a repeating group. Value must be positive.
        #       </fixr:documentation>
        #   </fixr:annotation>
        documentation = element.findall("./fixr:annotation/fixr:documentation/[@purpose='SYNOPSIS']", namespaces)
        if not documentation or len(documentation) == 0 or documentation[0].text is None:
            return ''
        return documentation[0].text.strip()
  

    def load_data_types(self, repository):
        # <fixr:datatypes>
        #   <fixr:datatype name="NumInGroup" baseType="int" added="FIX.4.3">
        #       <fixr:mappedDatatype standard="XML" base="xs:positiveInteger" builtin="0">
        #           <fixr:annotation>
        #               <fixr:documentation purpose="SYNOPSIS">
        #                   int field representing the number of entries in a repeating group. Value must be positive.
        #               </fixr:documentation>
        #           </fixr:annotation>
        #       </fixr:mappedDatatype>
        #       <fixr:annotation>
        #           <fixr:documentation purpose="SYNOPSIS">
        #               int field representing the number of entries in a repeating group. Value must be positive.
        #           </fixr:documentation>
        #       </fixr:annotation>
        #   </fixr:datatype>
        dataTypesElement = repository.find('fixr:datatypes', namespaces)
        for dataTypeElement in dataTypesElement.findall('fixr:datatype', namespaces):
            dataType = DataType(
                dataTypeElement.get('name'),
                dataTypeElement.get('baseType'),
                dataTypeElement.get('added'),
                self.extract_synopsis(dataTypeElement)
            )
            self.data_types[dataType.name] = dataType
        

    def load_code_sets(self, repository):
        # <fixr:codeSets>
        #   <fixr:codeSet name="AdvSideCodeSet" id="4" type="char">
        #       <fixr:code name="Buy" id="4001" value="B" sort="1" added="FIX.2.7">
        #           <fixr:annotation>
        #               <fixr:documentation purpose="SYNOPSIS">
        #                   Buy
        #               </fixr:documentation>
        #           </fixr:annotation>
        #       </fixr:code>
        codeSetsElement = repository.find('fixr:codeSets', namespaces)
        for codeSetElement in codeSetsElement.findall('fixr:codeSet', namespaces):
            codes = []
            for codeElement in codeSetElement.findall('fixr:code', namespaces):
                code = Code(
                    codeElement.get('id'),
                    codeElement.get('name'),
                    codeElement.get('value'),
                    codeElement.get('added'),
                    self.extract_synopsis(codeElement)
                )
                codes.append(code)
            code_set = CodeSet(
                codeSetElement.get('id'),
                codeSetElement.get('name'),
                codeSetElement.get('type'),
                self.extract_synopsis(codeSetElement),
                codes
            )
            self.code_sets[code_set.name] = code_set

    def load_fields(self, repository):
        # <fixr:fields>
		#   <fixr:field id="1" name="Account" type="String" added="FIX.2.7" abbrName="Acct">
		# 	    <fixr:annotation>
		# 		    <fixr:documentation purpose="SYNOPSIS">
        #               Account mnemonic as agreed between buy and sell sides, e.g. broker and institution or investor/intermediary and fund manager.
        #           </fixr:documentation>
		# 	    </fixr:annotation>
		#   </fixr:field>
        fieldsElement = repository.find('fixr:fields', namespaces)
        for fieldElement in fieldsElement.findall('fixr:field', namespaces):
            field = Field(
                int(fieldElement.get('id')),
                fieldElement.get('name'),
                fieldElement.get('type'),
                fieldElement.get('added'),
                self.extract_synopsis(fieldElement)
            )
            self.fields_by_tag[field.id] = field
            self.fields_by_name[field.name.lower()] = field

    def extract_references(self, element):
        references = []
        for refElement in list(element):
            if refElement.tag == '{{{}}}fieldRef'.format(namespaces['fixr']) or refElement.tag == '{{{}}}numInGroup'.format(namespaces['fixr']):
                reference = Reference(
                    int(refElement.get('id')),
                    None,
                    None,
                    refElement.get("presence"),
                    refElement.get('added'),
                    self.extract_synopsis(refElement)
                )
                references.append(reference)
            elif refElement.tag == '{{{}}}groupRef'.format(namespaces['fixr']):
                reference = Reference(
                    None,
                    refElement.get('id'),
                    None,
                    refElement.get("presence"),
                    refElement.get('added'),
                    self.extract_synopsis(refElement)
                )
                references.append(reference)
            elif refElement.tag == '{{{}}}componentRef'.format(namespaces['fixr']):
                reference = Reference(
                    None,
                    None,
                    refElement.get('id'),
                    refElement.get("presence"),
                    refElement.get('added'),
                    self.extract_synopsis(refElement)
                )
                references.append(reference)
            elif refElement.tag == '{{{}}}annotation'.format(namespaces['fixr']):
                # Don't care about these atleast for now
                pass
            else:
                raise Exception('Unexpected component element type {}'.format(refElement.tag))
        return references


    def load_components(self, repository):
        # <fixr:component name="DiscretionInstructions" id="1001" category="Common" added="FIX.4.4" abbrName="DiscInstr">
        #   <fixr:fieldRef id="388" added="FIX.4.4">
        #       <fixr:annotation>
        #           <fixr:documentation>
        #               What the discretionary price is related to (e.g. primary price, display price etc)
        #           </fixr:documentation>
        #       </fixr:annotation>
        #   </fixr:fieldRef>
        componentsElement = repository.find('fixr:components', namespaces)
        for componentElement in componentsElement.findall('fixr:component', namespaces):
            component = Component(
                componentElement.get('id'), 
                componentElement.get('name'), 
                componentElement.get('category'), 
                componentElement.get('added'),
                self.extract_synopsis(componentElement),
                self.extract_references(componentElement)
            )
            self.components[component.id] = component

    def load_groups(self, repository):
        # <fixr:groups>
        #   <fixr:group id="1007" added="FIX.4.4" name="LegStipulations" category="Common" abbrName="Stip">
        #       <fixr:numInGroup id="683"/>
        #       <fixr:fieldRef id="688" added="FIX.4.4">
        #           <fixr:annotation>
        #               <fixr:documentation>
        #                   Required if NoLegStipulations &gt;0
        #               </fixr:documentation>
        #           </fixr:annotation>
        #       </fixr:fieldRef>
        #       <fixr:fieldRef id="689" added="FIX.4.4">
        #           <fixr:annotation>
        #               <fixr:documentation/>
        #           </fixr:annotation>
        #       </fixr:fieldRef>
        #       <fixr:annotation>
        #           <fixr:documentation/>
        #       </fixr:annotation>
        #    </fixr:group>
        groupsElement = repository.find('fixr:groups', namespaces)
        for groupElement in groupsElement.findall('fixr:group', namespaces):
            group = Group(
                groupElement.get('id'),
                groupElement.get('name'),
                groupElement.get('added'),
                groupElement.get('category'),
                self.extract_synopsis(groupElement),
                self.extract_references(groupElement)
            )
            self.groups[group.id] = group    


    def load_messages(self, repository):
        # <fixr:messages>
        #   <fixr:message name="Heartbeat" id="1" msgType="0" category="Session" added="FIX.2.7" abbrName="Heartbeat">
        #       <fixr:structure>
        #           <fixr:componentRef id="1024" presence="required" added="FIX.2.7">
        #               <fixr:annotation>
        #                   <fixr:documentation>
        #                       MsgType = 0
        #                   </fixr:documentation>
        #               </fixr:annotation>
        #           </fixr:componentRef>
        messagesElement = repository.find('fixr:messages', namespaces)
        for messageElement in messagesElement.findall('fixr:message', namespaces):
            structureElement = messageElement.find('fixr:structure', namespaces)
            message = Message(
                messageElement.get('id'),
                messageElement.get('name'),
                messageElement.get('msgType'),
                messageElement.get('category'),
                messageElement.get('added'),
                self.extract_synopsis(messageElement),
                self.extract_references(structureElement)
            )
            self.messages[message.id] = message
            self.messages_by_msg_type[message.msg_type] = message
            self.messages_by_name[message.name.lower()] = message

    
    def create_xml_metadata(self, root):
        #     <fixr:metadata>
        #         <dc:title>Orchestra</dc:title>
        #         <dc:creator>unified2orchestra.xslt script</dc:creator>
        #         <dc:publisher>FIX Trading Community</dc:publisher>
        #         <dc:date>2019-03-12T10:11:48.582-05:00</dc:date>
        #         <dc:format>Orchestra schema</dc:format>
        #         <dc:source>FIX Unified Repository</dc:source>
        #     </fixr:metadata>
        metadata = ET.SubElement(root, '{%s}metadata' % (fixr_namespace))
        ET.SubElement(metadata, '{%s}title' % (dc_namespace)).text = 'Orchestra'
        ET.SubElement(metadata, '{%s}creator' % (dc_namespace)).text = 'https://github.com/GaryHughes/fixorchestra'
        ET.SubElement(metadata, '{%s}publisher' % (dc_namespace)).text = 'Gary Hughes'
        ET.SubElement(metadata, '{%s}date' % (dc_namespace)).text = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f UTC')
        ET.SubElement(metadata, '{%s}format' % (dc_namespace)).text = 'Orchestra schema'
        ET.SubElement(metadata, '{%s}source' % (dc_namespace)).text = 'FIX Unified Repository'


    def create_xml_data_types(self, root):
        # <fixr:datatypes>
        #   <fixr:datatype name="NumInGroup" baseType="int" added="FIX.4.3">
        #       <fixr:annotation>
        #           <fixr:documentation purpose="SYNOPSIS">
        #               int field representing the number of entries in a repeating group. Value must be positive.
        #           </fixr:documentation>
        #       </fixr:annotation>
        #   </fixr:datatype>
        data_types = ET.SubElement(root, '{%s}datatypes' % (fixr_namespace))
        for source in self.data_types.values():
            data_type = ET.SubElement(data_types, '{%s}datatype' % (fixr_namespace), name=source.name, added=source.added)
            if source.base_type:
                data_type.attrib['baseType'] = source.base_type
            annotation = ET.SubElement(data_type, '{%s}annotation' % (fixr_namespace))
            ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source.synopsis


    def create_xml_code_sets(self, root):
        # <fixr:codeSets>
        #   <fixr:codeSet name="AdvSideCodeSet" id="4" type="char">
        #       <fixr:code name="Buy" id="4001" value="B" sort="1" added="FIX.2.7">
        #           <fixr:annotation>
        #               <fixr:documentation purpose="SYNOPSIS">
        #                   Buy
        #               </fixr:documentation>
        #           </fixr:annotation>
        #       </fixr:code>
        code_sets = ET.SubElement(root, '{%s}codeSets' % (fixr_namespace))
        for source in self.code_sets.values():
            code_set = ET.SubElement(code_sets, '{%s}codeSet' % (fixr_namespace), name=source.name, id=str(source.id), type=source.type)
            for source_code in source.codes:
                # TODO sort attribute
                code = ET.SubElement(code_set, '{%s}code' % (fixr_namespace), name=source_code.name, id=str(source_code.id), value=source_code.value, added=source_code.added)
                annotation = ET.SubElement(code, '{%s}annotation' % (fixr_namespace))
                ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source_code.synopsis
            annotation = ET.SubElement(code_set, '{%s}annotation' % (fixr_namespace))
            ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source.synopsis
      

    def create_xml_fields(self, root):
        # <fixr:fields>
		#   <fixr:field id="1" name="Account" type="String" added="FIX.2.7" abbrName="Acct">
		# 	    <fixr:annotation>
		# 		    <fixr:documentation purpose="SYNOPSIS">
        #               Account mnemonic as agreed between buy and sell sides, e.g. broker and institution or investor/intermediary and fund manager.
        #           </fixr:documentation>
		# 	    </fixr:annotation>
		#   </fixr:field>      
        fields = ET.SubElement(root, '{%s}fields' % (fixr_namespace))
        for source in self.fields_by_tag.values():
            # TODO abbrName
            field = ET.SubElement(fields, '{%s}field' % (fixr_namespace), id=str(source.id), name=source.name, type=source.type, added=source.added)
            annotation = ET.SubElement(field, '{%s}annotation' % (fixr_namespace))
            ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source.synopsis


    def create_xml_references(self, root, references):
        #   <fixr:componentRef id="1024" presence="required" added="FIX.2.7">
        #               <fixr:annotation>
        #                   <fixr:documentation>
        #                       MsgType = 0
        #                   </fixr:documentation>
        #               </fixr:annotation>
        #           </fixr:componentRef>
        #           <fixr:fieldRef id="64" added="FIX.2.7">
	    #    		    <fixr:annotation>
	    # 			    	<fixr:documentation>
        #                       Required when SettlmntTyp = 6 (Future) or SettlmntTyp = 8 (Sellers Option)
        #                   </fixr:documentation>
	    # 				</fixr:annotation>
	    # 			</fixr:fieldRef>
        for reference in references:
            if reference.field_id:
                fieldRef = ET.SubElement(root, '{%s}fieldRef' % (fixr_namespace), id=str(reference.field_id), added=reference.added)
                if reference.presence:
                    fieldRef.attrib['presence'] = reference.presence
                annotation = ET.SubElement(fieldRef, '{%s}annotation' % (fixr_namespace))
                ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = reference.synopsis
            elif reference.component_id:
                componentRef = ET.SubElement(root, '{%s}componentRef' % (fixr_namespace), id=str(reference.component_id), added=reference.added)
                if reference.presence:
                    componentRef.attrib['presence'] = reference.presence
                annotation = ET.SubElement(componentRef, '{%s}annotation' % (fixr_namespace))
                ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = reference.synopsis
            elif reference.group_id:
                pass    


    def create_xml_components(self, root):
        # <fixr:component name="DiscretionInstructions" id="1001" category="Common" added="FIX.4.4" abbrName="DiscInstr">
        #   <fixr:fieldRef id="388" added="FIX.4.4">
        #       <fixr:annotation>
        #           <fixr:documentation>
        #               What the discretionary price is related to (e.g. primary price, display price etc)
        #           </fixr:documentation>
        #       </fixr:annotation>
        #   </fixr:fieldRef>
        components = ET.SubElement(root, '{%s}components' % (fixr_namespace))
        for source in self.components.values():
            # TODO abbrName
            component = ET.SubElement(components, '{%s}component' % (fixr_namespace), name=source.name, id=str(source.id), category=source.category, added=source.added)
            self.create_xml_references(component, source.references)
            annotation = ET.SubElement(component, '{%s}annotation' % (fixr_namespace))
            ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source.synopsis
         
   
    def create_xml_groups(self, root):
        # <fixr:groups>
        #   <fixr:group id="1007" added="FIX.4.4" name="LegStipulations" category="Common" abbrName="Stip">
        #       <fixr:numInGroup id="683"/>
        #       <fixr:fieldRef id="688" added="FIX.4.4">
        #           <fixr:annotation>
        #               <fixr:documentation>
        #                   Required if NoLegStipulations &gt;0
        #               </fixr:documentation>
        #           </fixr:annotation>
        #       </fixr:fieldRef>
        #       <fixr:fieldRef id="689" added="FIX.4.4">
        #           <fixr:annotation>
        #               <fixr:documentation/>
        #           </fixr:annotation>
        #       </fixr:fieldRef>
        #       <fixr:annotation>
        #           <fixr:documentation/>
        #       </fixr:annotation>
        #    </fixr:group>
        groups = ET.SubElement(root, '{%s}groups' % (fixr_namespace))



    def create_xml_messages(self, root):
        # <fixr:messages>
        #   <fixr:message name="Heartbeat" id="1" msgType="0" category="Session" added="FIX.2.7" abbrName="Heartbeat">
        #       <fixr:structure>
        #           <fixr:componentRef id="1024" presence="required" added="FIX.2.7">
        #               <fixr:annotation>
        #                   <fixr:documentation>
        #                       MsgType = 0
        #                   </fixr:documentation>
        #               </fixr:annotation>
        #           </fixr:componentRef>
        #           <fixr:fieldRef id="64" added="FIX.2.7">
	    #    		    <fixr:annotation>
	    # 			    	<fixr:documentation>
        #                       Required when SettlmntTyp = 6 (Future) or SettlmntTyp = 8 (Sellers Option)
        #                   </fixr:documentation>
	    # 				</fixr:annotation>
	    # 			</fixr:fieldRef>
        messages = ET.SubElement(root, '{%s}messages' % (fixr_namespace))
        for source in self.messages_by_msg_type.values():
            # TODO abbrName
            message = ET.SubElement(messages, '{%s}message' % (fixr_namespace), name=source.name, id=source.id, msgType=source.msg_type, category=source.category, added=source.added)
            structure = ET.SubElement(message, '{%s}structure' % (fixr_namespace))
            self.create_xml_references(structure, source.references)
            annotation = ET.SubElement(message, '{%s}annotation' % (fixr_namespace))
            ET.SubElement(annotation, '{%s}documentation' % (fixr_namespace), purpose='SYNOPSIS').text = source.synopsis


    def to_xml(self):
        # <?xml version="1.0" encoding="UTF-8"?>
        # <fixr:repository xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:functx="http://www.functx.com" xmlns:fixr="http://fixprotocol.io/2020/orchestra/repository" xmlns:dc="http://purl.org/dc/elements/1.1/" name="FIX.4.2" version="FIX.4.2" specUrl="http://www.fixprotocol.org/specifications/fix4.2spec" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        root = ET.Element('{%s}repository' % (fixr_namespace))
        
        self.create_xml_metadata(root)
        self.create_xml_data_types(root)
        self.create_xml_code_sets(root)
        self.create_xml_fields(root)
        self.create_xml_components(root)
        self.create_xml_groups(root)
        self.create_xml_messages(root)

        return root


def dump_field(orchestration, tag_or_name):
    try:
        field = orchestration.fields_by_tag[int(tag_or_name)]
    except (KeyError, ValueError):
        try:
            field = orchestration.fields_by_name[tag_or_name.lower()]
        except KeyError:
            print("Could not find a field with Tag or Name = '{}'".format(tag_or_name))
            return
    print(field.name + " {")
    print("    Id    = " + str(field.id))
    print("    Type  = " + field.type)
    print("    Added = " + field.added)
    print("    (" + field.synopsis + ")")
    try:
        code_set = orchestration.code_sets[field.type]
        print("    Values {")
        for code in code_set.codes:
            name = code.name
            print("        {} ({}, {}, {})".format(code.value, code.name, code.added, code.synopsis))
        print("    }")
    except KeyError:
        pass
    print("}")


def dump_references(orchestration, references, depth):
    padding = '    ' * depth
    for reference in references:
        if reference.field_id:
            field = orchestration.fields_by_tag[reference.field_id]
            print(padding + '{} (Id = {}, Type = {}, Added = {}, Presence = {})'.format(field.name, field.id, field.type, field.added, reference.presence))
        elif reference.group_id:
            group = orchestration.groups[reference.group_id]
            print(padding + group.name + " (Id = {}, Category = {}, Added = {}, Presence  = {}) {{".format(group.id, group.category, group.added, reference.presence))
            dump_references(orchestration, group.references, depth + 1)
            print(padding + "}")
        elif reference.component_id:
            component = orchestration.components[reference.component_id]
            print(padding + component.name + " (Id = {}, Category = {}, Added = {}, Presence = {}) {{".format(component.id, component.category, component.added, reference.presence))
            dump_references(orchestration, component.references, depth + 1)
            print(padding + "}")
            pass


def dump_message(orchestration, msg_type_or_name):
    try:
        message = orchestration.messages_by_msg_type[msg_type_or_name]
    except KeyError:
        try:
            message = orchestration.messages_by_name[msg_type_or_name.lower()]
        except KeyError:
            print("Could not find a message with MsgType or Name = '{}'".format(msg_type_or_name))
            return
    print(message.name + " {")
    print("    Id = " + message.id)
    print("    MsgType = " + message.msg_type)
    print("    Category = " + message.category)
    print("    Added = " + message.added)
    print("    (" + message.synopsis + ")")
    print("    References {")
    dump_references(orchestration, message.references, 2)
    print("    }")
    print("}")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--orchestration', required=True, metavar='file', help='The orchestration to load')
    parser.add_argument('--dump_field', required=False, metavar='(tag|name)' ,type=str, help='Display the definition of a field')
    parser.add_argument('--dump_message', required=False, metavar='(msgtype|name)', help='Display the definition of a message')
  
    args = parser.parse_args()

    orchestration = Orchestration(args.orchestration)

    if args.dump_field:
        dump_field(orchestration, args.dump_field)

    if args.dump_message:
        dump_message(orchestration, args.dump_message)
        



