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