import json
import os
from pathlib import Path

import cv2

import src.constants as constants
from natsort import natsorted


def kelvin_to_illumenant(kelvins):
    if isinstance(kelvins, str):
        if kelvins == '':
            return
        elif kelvins in list(constants.KELVINS_TABLE.keys()):
            return kelvins
        try:
            kelvins = int(''.join(filter(lambda x: x.isdigit(), kelvins)))
        except ValueError:
            print('Error is because of: ', kelvins)
            return

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


# Other utils
def get_list_average(list_in: list, min_index=None, max_index=None):
    if not isinstance(list_in, list):
        return

    if min_index is not None:
        if max_index is None:
            list_in = [list_in[min_index]]
        else:
            list_in = list_in[min_index:max_index]

    result = 0
    divider = 0

    for item in list_in:
        if isinstance(item, float) or isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
            if isinstance(item, str) and item.isdigit():
                result += int(item)
                divider += 1
                continue
            result += item
            divider += 1

    return result / divider


def compare_lists(list1, list2):
    return [str(s) for s in (set(list1) ^ set(list2))]


def parses_to_integer(s):
    return isinstance(s, int) or (isinstance(s, float) and s.is_integer())


def convert_to_int_float(s):
    if isinstance(s, str):
        if s.isdigit():
            s = float(s)
            if parses_to_integer(s):
                s = int(s)
    else:
        if isinstance(s, float) and parses_to_integer(s):
            s = int(s)
    return s


# Deeper stuff
def analyze_images_test_results(template_data):
    skipped_cases = []

    for test_type in template_data.keys():
        for light_temp in template_data[test_type].keys():
            for lux in template_data[test_type][light_temp].keys():
                img_file_path = template_data[test_type][light_temp][lux]['filename']
                img_file_name = os.path.basename(img_file_path)
                img_results_path = os.path.join(os.path.dirname(img_file_path), 'Results')

                if not os.path.isdir(img_results_path):
                    skipped_cases.append({
                        'test_type': test_type,
                        'light_temp': light_temp,
                        'lux': lux,
                        'reason': f'{img_results_path} is not a dir!'
                    })
                    print(f'Not found: {img_results_path}\nSkipping!')
                    continue

                img_json_filename = [f for f in natsorted(os.listdir(img_results_path)) if
                                     f.startswith(img_file_name.split('.')[0]) and f.endswith('.json')]

                if len(img_json_filename) < 1:
                    continue

                img_json_file = os.path.join(img_results_path, img_json_filename[0])
                if not os.path.isfile(img_json_file):
                    skipped_cases.append({
                        'test_type': test_type,
                        'light_temp': light_temp,
                        'lux': lux,
                        'reason': f'{img_json_file} is not a file!'
                    })
                    print(f'Not found: {img_results_path}\nSkipping!')
                    continue

                with open(img_json_file) as json_file:
                    image_analysis_readable = json.load(json_file)
                image_analysis_readable = image_analysis_readable[list(image_analysis_readable.keys())[0]]

                keyerr = False
                for param in template_data[test_type][light_temp][lux]['params'].keys():
                    params_depth = param.split('>')
                    for num, param_piece in enumerate(params_depth):
                        if num == 0:
                            # At beginning set equal to parent of param (possibly)
                            try:
                                param_val = image_analysis_readable[param_piece]
                            except KeyError:
                                keyerr = True

                        elif num != len(params_depth) - 1 and not keyerr:
                            # If not at end yet and not at beginning
                            param_val = param_val[param_piece]

                        if num == len(params_depth) - 1:
                            # If last one -> return
                            # Full name of param: param,
                            # last part of param: param_piece,
                            # param value: param_val
                            if keyerr:
                                skipped_cases.append({
                                    'test_type': test_type,
                                    'light_temp': light_temp,
                                    'lux': lux,
                                    'param': param,
                                    'results_file': img_json_file,
                                    'reason': f'{param} parameter missing in Results file!'
                                })
                                continue

                            if len(params_depth) > 1:
                                param_val = param_val[param_piece]

                            curr_param_dict = template_data[test_type][light_temp][lux]["params"][param]

                            try:
                                restrict_start = int(curr_param_dict['start_value']) - 1
                            except KeyError:
                                restrict_start = None

                            try:
                                restrict_end = int(curr_param_dict['end_value']) - 1
                            except KeyError:
                                restrict_end = None

                            param_val_calc = get_list_average(
                                param_val,
                                restrict_start,
                                restrict_end
                            )

                            try:
                                if curr_param_dict['absolute_value_bool']:
                                    param_val_calc = abs(param_val_calc)
                            except KeyError:
                                pass

                            curr_param_dict['result'] = param_val
                            curr_param_dict['result_calculated'] = param_val_calc

                            print(f'param {param} is: ', param_val)
                            print(f'calculated value is: {param_val_calc}')
                            print(f'min is: {curr_param_dict["min"]}')
                            print(f'max is: {curr_param_dict["max"]}')
                            if curr_param_dict["min"] < param_val_calc < curr_param_dict["max"]:
                                curr_param_dict['result_pass_bool'] = True
                                print('PASS!\n')
                            else:
                                curr_param_dict['result_pass_bool'] = False
                                print('FAIL!\n')

    return template_data, skipped_cases


def add_filenames_to_data(template_data, img_dir):
    file_exts = [
        'png', 'jpg', 'mp4'
    ]

    if os.path.isdir(img_dir):
        img_dir = os.path.normpath(img_dir)

        for test_type in list(template_data.keys()):
            for light_temp in list(template_data[test_type].keys()):
                for lux in list(template_data[test_type][light_temp].keys()):
                    try:
                        template_data[test_type][light_temp][lux]['filename']
                    except KeyError:
                        filepath = None
                        for ext in file_exts:
                            filepath = os.path.join(img_dir, test_type, light_temp,
                                                    f'{test_type}_{light_temp}_{lux}.{ext}')
                            if os.path.exists(filepath):
                                break
                        if filepath is not None:
                            template_data[test_type][light_temp][lux]['filename'] = filepath
                        else:
                            template_data[test_type][light_temp][lux]['filename'] = None


def extract_video_frame(videofile, start_frame, number_of_frames=None, end_frame=None, skip_frames=0, subfolder=False):
    output = []

    file_name = os.path.basename(videofile)
    file_path = os.path.dirname(videofile)

    if subfolder:
        file_path = os.path.join(file_path, subfolder)
        # Create dirs if not exist
        Path(file_path).mkdir(parents=True, exist_ok=True)


    vidcap = cv2.VideoCapture(videofile)
    success, image = vidcap.read()

    current_frame = 1

    next_frame = start_frame

    img_out = []

    if end_frame is None:
        end_frame = start_frame + (number_of_frames * skip_frames) - 1
    else:
        print("end frame is: ", end_frame)
        if start_frame > end_frame:
            print('Start frame must be smaller int than end frame!')
            return
    print()
    while success:
        if start_frame <= current_frame <= end_frame:
            if skip_frames:
                if next_frame == 1:
                    next_frame = current_frame + skip_frames
                if current_frame == next_frame:
                    img_out = os.path.join(file_path, f"{file_name}_frame{current_frame}.jpg")
                    output.append(img_out)
                    cv2.imwrite(img_out, image)  # save frame as JPEG file

                    next_frame += skip_frames
            else:
                img_out = os.path.join(file_path, f"{file_name}_frame{current_frame}.jpg")
                output.append(img_out)
                cv2.imwrite(img_out, image)  # save frame as JPEG file
        elif start_frame <= current_frame:
            break

        # Save some time..
        if number_of_frames is not None:
            if len(img_out) == number_of_frames:
                break
        elif current_frame >= end_frame:
            break

        success, image = vidcap.read()
        print('Read a new frame: ', success)
        current_frame += 1

    return output
