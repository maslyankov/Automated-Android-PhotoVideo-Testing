from datetime import datetime

import xml.etree.ElementTree as ET
import src.constants as constants
from src.gui.utils_gui import Tree


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
def _convert_dict_to_xml_recurse(parent, dictitem):
    assert type(dictitem) is not type([])
    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.items():
            tag = str(tag).replace(' ', '')

            if type(child) is type([]):
                print(child.tag)
                # iterate through the array and convert
                for listchild in child:
                    elem = ET.Element(tag)
                    parent.append(elem)
                    _convert_dict_to_xml_recurse(elem, listchild)
            else:
                try:
                    child['params']
                except (TypeError, KeyError):
                    elem = ET.Element(tag)
                else:
                    elem = ET.Element(parent.tag)
                    elem.set('lux', tag)
                    print(f'parent tag {parent.tag}, tag {tag}')
                parent.append(elem)
                _convert_dict_to_xml_recurse(elem, child)
    else:
        parent.text = str(dictitem).strip(' ')


def convert_dict_to_xml(xmldict, name='root', file_is_new=False):
    """

    Converts a dictionary to an XML ElementTree Element

    """
    print('input dict: \n', xmldict, '\n')
    root = ET.Element(name)

    xmldata = {}

    if file_is_new:
        xmldata['time_created'] = str(datetime.now())
    xmldata['time_updated'] = str(datetime.now())
    xmldata['proj_req'] = xmldict

    _convert_dict_to_xml_recurse(root, xmldata)

    ret = ET.tostring(root)

    return ret


def merge_dicts(a, b, path=None):
    "merges b into a recursively "
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def dict_vals_to_int(d):
    for key in d.keys():
        try:
            if d[key].isdigit():
                d[key] = int(d[key])
        except AttributeError:
            pass
    return d


def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()

    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict_vals_to_int(dict(node.items())))

    for child in node:
        current = (None, None)
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        child_key = int(child.tag) if child.tag.isdigit() else child.tag

        if child.tag in nodedict.keys():
            # found duplicate tag, force a list
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
                    nodedict[child_key][curr_key] = merge_dicts(nodedict[child_key][curr_key], newitem)
                except KeyError:
                    nodedict[child_key][curr_key] = newitem
        else:
            # only one, directly set the dictionary
            try:
                child.attrib['lux']
            except KeyError:
                nodedict[child_key] = newitem
            else:
                curr_key = int(child.attrib['lux']) if child.attrib['lux'].isdigit() else child.attrib['lux']
                nodedict[child_key] = {}
                nodedict[child_key][curr_key] = newitem

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


def ConvertXMLFileToDict(filepath):
    xml_root = ET.parse(filepath).getroot()
    return ConvertXmlToDict(xml_root)


def dict_to_tree(dict_in):
    pass
