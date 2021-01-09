import xml.etree.ElementTree as ET
from datetime import datetime

# Local
from src import constants
from src.logs import logger
from src.app.utils import parses_to_integer


# XML Utils
def generate_sequence(subelem):
    seq_temp = []

    logger.info("Generating Sequence")

    for action_num, action in enumerate(subelem):

        action_list = []
        data_list = []

        # self.shoot_photo_seq.append(action.tag)
        for action_elem_num, action_elem in enumerate(action):
            # import pdb; pdb.set_trace()
            logger.debug(f"action elem: {action_elem}")
            logger.debug(f"data_list before {data_list}")
            if action_elem.tag == 'id':
                action_list.append(action_elem.text)
                logger.debug(f"Elem num: {action_elem_num}, elem text: {action_elem.text}")

            elif action_elem.tag == 'description':
                logger.debug(f'description: {action_elem.text}')
                if action_elem.text is not None:
                    data_list.append(action_elem.text)
                else:
                    data_list.append('')

            elif action_elem.tag == 'coordinates':
                coords_list = []

                for inner_num, inner in enumerate(action_elem):
                    # list should be: self.shoot_photo_seq = [
                    # ['element_id', ['Description', [x, y], 'tap' ] ]
                    # ]
                    coords_list.append(inner.text)
                data_list.append(coords_list)

            elif action_elem.tag == 'value':
                data_list.append(action_elem.text)

            logger.debug(f"data_list after {data_list}")
        try:
            data_list.append(action.attrib["type"])  # Set type
        except KeyError:
            logger.error("Error! Invalid XML!")

        action_list.append(data_list)

        seq_temp.append(action_list)
        logger.debug(f'Generated list for action: {action_list}')
    return seq_temp


def xml_from_sequence(obj, prop, xml_obj):
    for action in getattr(obj, prop):
        elem = ET.SubElement(xml_obj, "action")
        elem_id = ET.SubElement(elem, "id")  # set
        elem_desc = ET.SubElement(elem, "description")  # set

        elem.set('type', action[1][2])
        if action[1][2] == 'tap':  # If we have coords set, its a tap action
            elem_coordinates = ET.SubElement(elem, "coordinates")

            x = ET.SubElement(elem_coordinates, "x")  # set
            y = ET.SubElement(elem_coordinates, "y")  # set

            # list should be: self.shoot_photo_seq = [
            # ['element_id', ['Description', [x, y] , type] ]
            # ]
            elem_id.text = str(action[0])
            elem_desc.text = str(action[1][0])
            x.text = str(action[1][1][0])
            y.text = str(action[1][1][1])
        else:
            elem_id.text = str(action[0])
            elem_desc.text = str(action[1][0])
            elem_value = ET.SubElement(elem, "value")
            elem_value.text = str(action[1][1])


def _convert_dict_to_xml_recurse(parent, dictitem, parent_tag=None):
    elem_tag = None
    assert type(dictitem) is not type([])

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
        parent.text = str(dictitem).strip(' ')


def convert_dict_to_xml(xmldict, name='root', file_is_new=False):
    """

    Converts a dictionary to an XML ElementTree Element

    """
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
                logger.error('Conflict at %s' % '.'.join(path + [str(key)]))
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
        logger.error('Expected ElementTree.Element or file path string')
        raise TypeError('Expected ElementTree.Element or file path string')
    return {root.tag: _convert_xml_to_dict_recurse(root, dictclass)}
