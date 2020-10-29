import xml.etree.ElementTree as ET
from datetime import datetime

# Local
import src.constants as constants


# XML Utils
def _convert_dict_to_xml_recurse(parent, dictitem, parent_tag=None):
    elem_tag = None
    assert type(dictitem) is not type([])

    print('dsadsa ', parent.tag, type(dictitem))

    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.items():
            tag = str(tag).replace(' ', '')
            if type(child) is type([]):
                # iterate through the array and convert
                for listchild in child:
                    elem = ET.Element(tag)
                    parent.append(elem)
                    _convert_dict_to_xml_recurse(elem, listchild)
            else:
                is_light = tag in constants.KELVINS_TABLE.keys() or tag.endswith('K')
                try:
                    child['params']
                except (TypeError, KeyError):
                    if parent.tag == 'params':
                        elem = ET.Element('param')
                        elem.set('name', tag)
                    else:
                        elem = ET.Element(tag)
                        # print('except elem tag: ', tag, ' parent: ', parent.tag, ' child: ', child)
                else:
                    elem = ET.Element('light')
                    elem.set('color', parent_tag)
                    elem.set('lux', tag)
                    # print(f'color (parent) {parent.tag}, lux (tag): {tag}')
                if not is_light:
                    parent.append(elem)
                else:
                    elem = parent
                    elem_tag = tag
                _convert_dict_to_xml_recurse(elem, child, elem_tag)
    else:
        print(parent.text, ' getss ', str(dictitem).strip(' '))
        parent.text = str(dictitem).strip(' ')


def parses_to_integer(s):
    return isinstance(s, int) or (isinstance(s, float) and s.is_integer())


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
    """merges b into a recursively """
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


def dict_vals_to_int(d, fltr=None):
    d_out = {}
    for key in d.keys():
        if key not in fltr:
            try:
                if d[key].isdigit():
                    d_out[key] = int(d[key])
                else:
                    d_out[key] = d[key]
            except AttributeError:
                pass
    return d_out


def _convert_xml_to_dict_recurse(node, dictclass):
    nodedict = dictclass()

    if node.tag == 'light':
        par_key = node.attrib['color']
    elif node.tag == 'param':
        par_key = node.attrib['name']
    else:
        par_key = node.tag

    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict_vals_to_int(dict(node.items()), fltr=['name', 'color', 'lux', 'value']))

    for child in node:
        # recursively add the element's children
        newitem = _convert_xml_to_dict_recurse(child, dictclass)
        child_key = int(child.tag) if child.tag.isdigit() else child.tag

        if child.tag in nodedict.keys():
            if child.tag == 'light':
                try:
                    nodedict[par_key][child_key] = newitem
                except KeyError:
                    pass
            elif child.tag == 'param':
                pass
        else:
            # only one, directly set the dictionary
            if child.tag == 'light':
                temp_key = child.attrib['color']
                curr_key = int(child.attrib['lux']) if child.attrib['lux'].isdigit() else child.attrib['lux']
                try:
                    nodedict[temp_key][curr_key] = newitem
                except KeyError:
                    nodedict[temp_key] = {}
                    nodedict[temp_key][curr_key] = newitem
            elif child.tag == 'param':
                param_key = child.attrib['name']
                try:
                    nodedict[param_key] = newitem
                except KeyError:
                    nodedict = {param_key: newitem}
            else:
                nodedict[child_key] = newitem

    if node.text is None:
        text = ''
    else:
        text = node.text.strip()

    if len(nodedict) <= 0:
        try:
            text = float(text)
            if parses_to_integer(text):
                text = int(text)
        except ValueError:
            pass
        # if we don't have child nodes or attributes, just set the text
        nodedict = text
    return nodedict


def convert_xml_to_dict(root, dictclass=dict):
    """
    Converts an XML file or ElementTree Element to a dictionary

    """
    # If a string is passed in, try to open it as a file

    if type(root) == type('') or type(root) == type(u''):
        root = ET.parse(root).getroot()  # ET.fromstring(root)
    elif not isinstance(root, ET.Element):
        raise TypeError('Expected ElementTree.Element or file path string')
    return {root.tag: _convert_xml_to_dict_recurse(root, dictclass)}
