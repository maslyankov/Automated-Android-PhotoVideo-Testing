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

# XML
import xml.etree.ElementTree as ET
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

def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    Source : http://stackoverflow.com/questions/17402323/use-xml-etree-elementtree-to-write-out-nicely-formatted-xml-files
    """
    from xml.dom import minidom
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="".join([' '] * 4))