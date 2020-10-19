from datetime import datetime

import src.constants as constants



def kelvin_to_illumenant(kelvins):
    if isinstance(kelvins, str):
        if kelvins == '':
            return
        try:
            kelvins = int(''.join(filter(lambda x: x.isdigit(), kelvins)))
        except ValueError:
            print('Error is because of: ', kelvins)

    if isinstance(kelvins, int):
        for temp in constants.KELVINS_TABLE:
            if abs(kelvins - constants.KELVINS_TABLE[temp][0]) < 20:
                return temp
        return f"{kelvins}K"
    else:
        raise ValueError('Wrong input!', str(kelvins), str(type(kelvins)))


def illumenant_to_kelvin(illum):
    try:
        return constants.KELVINS_TABLE[illum][0]
    except KeyError:
        print('Illumenant not found.')
        return illum


def only_digits(val) -> int:
    if isinstance(val, str):
        return int(''.join(filter(lambda x: x.isdigit(), val)))
    elif isinstance(val, int):
        return val


def only_chars(val: str) -> int:
    if isinstance(val, str):
        return ''.join(filter(lambda x: x.isalpha(), val))

# XML Utils
import xml.etree.ElementTree as ET
def ConvertDictToXml(xmldict, name='root', file_is_new=False):

    """

    Converts a dictionary to an XML ElementTree Element

    """
    print('input dict: \n', xmldict, '\n')
    root = ET.Element(name)
    if file_is_new:
        root.set('time_created', str(datetime.now()))
    root.set('time_updated', str(datetime.now()))

    _ConvertDictToXmlRecurse(root, xmldict)

    ret = ET.tostring(root)

    return ret


def _ConvertDictToXmlRecurse(parent, dictitem):
    assert type(dictitem) is not type([])
    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.items():
            tag = str(tag).replace(' ', '')

            if type(child) is type([]):
                # iterate through the array and convert
                for listchild in child:
                    elem = ET.Element(tag)
                    parent.append(elem)
                    _ConvertDictToXmlRecurse(elem, listchild)
            else:
                elem = ET.Element(tag)
                parent.append(elem)
                _ConvertDictToXmlRecurse(elem, child)
    else:
        parent.text = str(dictitem).strip(' ')

def ConvertXMLFileToDict(filepath):
    xml_root = ET.parse(filepath).getroot()
    return ConvertXmlToDict(xml_root)

def ConvertXmlToDict(root, dictclass=dict):
    """
    Converts an XML file or ElementTree Element to a dictionary

    """
    # If a string is passed in, try to open it as a file

    if type(root) == type('') or type(root) == type(u''):
        root = ET.fromstring(root)

    elif not isinstance(root, ET.Element):
        raise TypeError('Expected ElementTree.Element or file path string')
    return {root.tag: _ConvertXmlToDictRecurse(root, dictclass)}


def merge_dicts(a, b, path=None):
    "merges b into a recursively"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()

    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))

    for child in node:
        current = (None, None)
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        print(child.tag, )
        if child.tag in nodedict.keys():
            # found duplicate tag, force a list
            #print('child tag: ', child.tag)
            try:
                child.attrib['lux']
            except KeyError:
                # append to existing list
                # Rare case
                nodedict[child.tag].append(newitem)
            else:
                curr_key = int(child.attrib['lux']) if child.attrib['lux'].isdigit() else child.attrib['lux']
                try:
                    # Key appears multiple times -> merge recursively
                    nodedict[child.tag][curr_key] = merge_dicts(nodedict[child.tag][curr_key], newitem)
                except KeyError:
                    print('else except keyerror1', child.tag)
                    nodedict[child.tag][curr_key] = newitem
        else:
            print('if else')
            # only one, directly set the dictionary
            print('one: ', newitem)
            try:
                child.attrib['lux']
            except KeyError:
                print('except keyerror2', child.tag)
                nodedict[child.tag] = newitem
            else:
                curr_key = int(child.attrib['lux']) if child.attrib['lux'].isdigit() else child.attrib['lux']
                print('else except keyerror2', child.tag, curr_key)
                nodedict[child.tag] = {}
                nodedict[child.tag][curr_key] = newitem

    if node.text is None:
        text = ''
    else:
        text = node.text.strip()

    if len(nodedict) > 0:
        # if we have a dictionary add the text as a dictionary value (if there is any)

        if len(text) > 0:
            try:
                text = float(text)
            except ValueError:
                pass
            nodedict['_text'] = text
    else:
        try:
            text = float(text)
        except ValueError:
            pass
        # if we don't have child nodes or attributes, just set the text
        nodedict = text

    return nodedict
