

def kelvin_to_illumenant(kelvins):
    if isinstance(kelvins, str):
        if kelvins == '':
            return
        try:
            kelvins = int(''.join(filter(lambda x: x.isdigit(), kelvins)))
        except ValueError:
            print('Error is because of: ', kelvins)

    if isinstance(kelvins, int):
        if abs(kelvins-2700) < 20:
            return 'WW'
        if abs(kelvins-2856) < 20:
            # Incandescent - typical, domestic, tungsten-filament lighting
            return 'A'
        elif abs(kelvins-3000) < 20:
            # F11 fluorescent narrow tri-band
            return 'TL83'
        elif abs(kelvins-3500) < 20:
            # F11 fluorescent narrow tri-band
            return 'TL835'
        elif abs(kelvins-4100) < 120:
            # Warm White Fluorescent
            return 'TL84'
        elif abs(kelvins-4230) < 20:
            # F2 cool white fluorescent
            return 'CWF'
        elif abs(kelvins-5000) < 20:
            return 'D50'
        elif abs(kelvins-5500) < 20:
            return 'D55'
        elif abs(kelvins-6500) < 20:
            # broad-band fluorescent lamp
            return 'D65'
        elif abs(kelvins-6770) < 20:
            return 'C'
        elif abs(kelvins-7500) < 20:
            return 'D75'
        else:
            return f"{kelvins}K"
    else:
        raise ValueError('Wrong input!', str(kelvins), str(type(kelvins)))


def only_digits(val) -> int:
    if isinstance(val, str):
        return int(''.join(filter(lambda x: x.isdigit(), val)))
    elif isinstance(val, int):
        return val


def only_chars(val: str) -> int:
    if isinstance(val, str):
        return ''.join(filter(lambda x: x.isalpha(), val))