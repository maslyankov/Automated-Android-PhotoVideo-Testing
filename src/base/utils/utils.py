import json
from os import path, listdir
from pathlib import Path
from hurry.filesize import size
from re import sub, match

import cv2
from natsort import natsorted

from src import constants
from src.logs import logger


def kelvin_to_illumenant(kelvins):
    if isinstance(kelvins, str):
        if kelvins == '':
            return
        elif kelvins in list(constants.KELVINS_TABLE.keys()):
            return kelvins
        try:
            kelvins = int(''.join(filter(lambda x: x.isdigit(), kelvins)))
        except ValueError:
            logger.error(f'Error is because of: {kelvins}')
            return

    if isinstance(kelvins, int):
        for temp in constants.KELVINS_TABLE:
            if abs(kelvins - constants.KELVINS_TABLE[temp][0]) < 20:
                return temp
        return f"{kelvins}K"
    else:
        logger.critical(f'Wrong input! {str(kelvins)}, {str(type(kelvins))}')
        raise ValueError(f'Wrong input! {str(kelvins), str(type(kelvins))}')


def illumenant_to_kelvin(illum):
    try:
        return constants.KELVINS_TABLE[illum][0]
    except KeyError:
        logger.error('Illumenant not found.')
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
    """
    Returns an average of all the items in passed list or of those between index min and max
    :param list_in:
    :param min_index:
    :param max_index:
    :return:
    """
    if not isinstance(list_in, list) and len(list_in) == 0:
        return

    if min_index is not None:
        if max_index is None:
            list_in = [list_in[min_index]]
        else:
            list_in = list_in[min_index:max_index]

    result = 0.0
    divider = 0

    for item in list_in:
        if isinstance(item, float) or isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
            if isinstance(item, str) and item.isdigit():
                result += float(item)
                divider += 1
                continue
            result += item
            divider += 1
    if result == 0 or divider == 0:
        return 0.0

    return result / divider


def get_file_paths(line_list, f_pattern):
    file_paths = list()
    path = sub(r"\:", "/", line_list[0])

    while len(line_list) > 1:
        if match(f_pattern, line_list[1]):
            file_paths.append(path + line_list[1])
            line_list.pop(0)

        else:
            return file_paths

    if match(f_pattern, line_list[0]):
        file_paths.append(path + line_list[0])
        line_list.pop(0)
        return file_paths

    line_list.pop(0)


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


def pretty_size(num: int):
    return size(num) if num else "-"


# Deeper stuff
def analyze_images_test_results(template_data, gen_summary = True):
    skipped_cases = list()
    if gen_summary:
        summary = dict()

    for test_type in template_data.keys():
        if gen_summary:
            summary[test_type] = dict()

        for light_temp in template_data[test_type].keys():
            if gen_summary:
                summary[test_type][light_temp] = dict()

            for lux in template_data[test_type][light_temp].keys():
                img_file_path = template_data[test_type][light_temp][lux]['filename']
                img_file_name = path.basename(img_file_path)
                img_results_path = path.join(path.dirname(img_file_path), 'Results')

                if not path.isdir(img_results_path):
                    skipped_cases.append({
                        'test_type': test_type,
                        'light_temp': light_temp,
                        'lux': lux,
                        'reason': f'{img_results_path} is not a dir!'
                    })
                    logger.warn(f'Not found: {img_results_path}\nSkipping!')
                    continue

                img_json_filename = [f for f in natsorted(listdir(img_results_path)) if
                                     f.startswith(img_file_name.split('.')[0]) and f.endswith('.json')]

                if len(img_json_filename) < 1:
                    continue

                img_json_file = path.join(img_results_path, img_json_filename[0])
                if not path.isfile(img_json_file):
                    skipped_cases.append({
                        'test_type': test_type,
                        'light_temp': light_temp,
                        'lux': lux,
                        'reason': f'{img_json_file} is not a file!'
                    })
                    logger.warn(f'Not found: {img_results_path}\nSkipping!')
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
                                if param != 'y_shading_corners_mean_percent':
                                    skipped_cases.append({
                                        'test_type': test_type,
                                        'light_temp': light_temp,
                                        'lux': lux,
                                        'param': param,
                                        'results_file': img_json_file,
                                        'reason': f'{param} parameter missing in Results file!'
                                    })
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

                            if param != 'y_shading_corners_mean_percent':
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
                            else:
                                keyerr = False

                                shading_max = image_analysis_readable['max_norml_pxl_level'][0]
                                logger.debug(f"Max = {shading_max}")
                                shading_mean = image_analysis_readable['resTable_Y_Luminance'][-3]
                                logger.debug(f"Mean = {shading_mean}")
                                param_val_calc = (shading_mean/shading_max * 100).__round__(2)
                                logger.debug(f"Calculated percentage: {param_val_calc}%")

                            try:
                                curr_param_dict['or_equal_bool']
                            except KeyError:
                                curr_param_dict['or_equal_bool'] = False

                            curr_param_dict['result'] = param_val
                            curr_param_dict['result_calculated'] = param_val_calc

                            logger.debug(f"{test_type}/{light_temp}/{lux}/{param} is: '{str(param_val)}', calc: {param_val_calc} ")
                            try:
                                logger.debug(f'min is: {curr_param_dict["min"]}')
                            except KeyError:
                                curr_param_dict["min"] = None
                            try:
                                logger.debug(f'max is: {curr_param_dict["max"]}')
                            except KeyError:
                                curr_param_dict["max"] = None

                            try:
                                if curr_param_dict["min"] and curr_param_dict["max"]:
                                    if curr_param_dict['or_equal_bool']:
                                        curr_param_check = curr_param_dict["min"] <= param_val_calc <= curr_param_dict["max"]
                                    else:
                                        curr_param_check = curr_param_dict["min"] < param_val_calc < curr_param_dict["max"]
                                elif curr_param_dict["min"]:
                                    if curr_param_dict['or_equal_bool']:
                                        curr_param_check = curr_param_dict["min"] <= param_val_calc
                                    else:
                                        curr_param_check = curr_param_dict["min"] < param_val_calc
                                elif curr_param_dict["max"]:
                                    if curr_param_dict['or_equal_bool']:
                                        curr_param_check = param_val_calc <= curr_param_dict["max"]
                                    else:
                                        curr_param_check = param_val_calc < curr_param_dict["max"]
                                else:
                                    curr_param_check = True
                            except TypeError as e:
                                skipped_cases.append({
                                    'test_type': test_type,
                                    'light_temp': light_temp,
                                    'lux': lux,
                                    'param': param,
                                    'results_file': img_json_file,
                                    'reason': f'{e}'
                                })
                                continue

                            if curr_param_check is True:
                                curr_param_dict['result_pass_bool'] = True
                                logger.debug(f"{test_type}/{light_temp}/{lux}/{param} -> PASS!\n")

                                if gen_summary:
                                    try:
                                        summary[test_type][light_temp]["pass"]
                                    except KeyError:
                                        summary[test_type][light_temp]["pass"] = 1
                                    else:
                                        summary[test_type][light_temp]["pass"] += 1
                            else:
                                curr_param_dict['result_pass_bool'] = False
                                logger.debug(f" -> FAIL!\n")

                                if gen_summary:
                                    try:
                                        summary[test_type][light_temp]["fail"]
                                    except KeyError:
                                        summary[test_type][light_temp]["fail"] = 1
                                    else:
                                        summary[test_type][light_temp]["fail"] += 1

    return template_data, skipped_cases, summary


def add_filenames_to_data(template_data, img_dir):
    file_exts = [
        'png', 'jpg', 'mp4'
    ]

    if path.isdir(img_dir):
        img_dir = path.normpath(img_dir)

        for test_type in list(template_data.keys()):
            for light_temp in list(template_data[test_type].keys()):
                for lux in list(template_data[test_type][light_temp].keys()):
                    try:
                        template_data[test_type][light_temp][lux]['filename']
                    except KeyError:
                        filepath = None
                        for ext in file_exts:
                            filepath = path.join(img_dir, test_type, light_temp,
                                                    f'{test_type}_{light_temp}_{lux}.{ext}')
                            if path.exists(filepath):
                                break
                        if filepath is not None:
                            template_data[test_type][light_temp][lux]['filename'] = filepath
                        else:
                            template_data[test_type][light_temp][lux]['filename'] = None


def extract_video_frame(videofile, start_frame, number_of_frames=None, end_frame=None, skip_frames=0,
                        subfolder=False, out_format="JPEG"):
    output = []

    formats = {
        "JPEG": "jpg",
        "PNG": "png"
    }

    file_name = path.basename(videofile)
    file_path = path.dirname(videofile)

    if subfolder:
        file_path = path.join(file_path, subfolder)
        # Create dirs if not exist
        Path(file_path).mkdir(parents=True, exist_ok=True)

    vidcap = cv2.VideoCapture(videofile)
    success, image = vidcap.read()

    current_frame = 1

    next_frame = start_frame

    img_out = []

    if end_frame is None or end_frame == 0:
        end_frame = start_frame + ((number_of_frames * skip_frames) if skip_frames else number_of_frames) - 1
    else:
        logger.info(f"end frame is: {end_frame}")
        if start_frame > end_frame:
            logger.error('Start frame must be smaller int than end frame!')
            return

    while success:
        if start_frame <= current_frame <= end_frame:
            if skip_frames:
                if current_frame == next_frame:
                    img_out = path.join(file_path, f"{file_name}_frame{current_frame}.{formats[out_format]}")
                    output.append(img_out)
                    cv2.imwrite(img_out, image)  # save frame as JPEG file

                    next_frame += skip_frames
            else:
                img_out = path.join(file_path, f"{file_name}_frame{current_frame}.{formats[out_format]}")
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
        logger.debug(f'Read a new frame: {success}')
        current_frame += 1

    return output


def get_video_info(video_in):
    cap = cv2.VideoCapture(video_in)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    logger.debug(f"Width: {w}, height: {h}, fps: {fps}, nframes: {n_frames}")
    return w, h, fps, n_frames


# Splits video in half
def split_video(video_in):
    w, h, fps, n_frames = get_video_info(video_in)

    x, y = 0, 0
    height = int(h/2)
    width = w

    logger.debug(f"split video got file: {video_in}")
    logger.debug(f"height: {height}, width: {width}, fps: {fps}, n_frames: {n_frames}")

    # (x, y, w, h) = cv2.boundingRect(c)
    # cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 20)
    # roi = frame[y:y+h, x:x+w]
    cap = cv2.VideoCapture(video_in)
    # get fps info from file CV_CAP_PROP_FPS, if possible
    fps = int(round(cap.get(5)))
    # check if we got a value, otherwise use any number - you might need to change this
    if fps == 0:
        fps = 30  # so change this number if cropped video has stange steed, higher number gives slower speed

    vid_name = path.basename(video_in)
    vid_name_no_ext = vid_name.split(".")[0]

    out_cropped = f"{vid_name_no_ext}_cropped"
    logger.info(f"cropping {vid_name} to {out_cropped}")

    out_path = f'{path.dirname(video_in)}/{out_cropped}.mp4'
    logger.debug(f"Is file: {path.isfile(out_path)}")

    suff = 1

    check_path = out_path

    while path.isfile(check_path):
        logger.debug(f"Checking {check_path}")

        check_path = f"{out_path.split('.')[0]}_{suff}.mp4"
        suff += 1

    out_path0 = f"{check_path.split('.')[0]}_top.mp4"
    out_path1 = f"{check_path.split('.')[0]}_bottom.mp4"
    logger.debug(f'Saving to {out_path0}')
    logger.debug(f'Saving to {out_path1}')

    # output_movie = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc('M','J','P','G'), fps, (width,height))
    output_movie0 = cv2.VideoWriter(out_path0, cv2.VideoWriter_fourcc(*'MP4V'), fps, (width, height))
    output_movie1 = cv2.VideoWriter(out_path1, cv2.VideoWriter_fourcc(*'MP4V'), fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        # (height, width) = frame.shape[:2]
        if frame is not None:
            curr_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            # Crop frame
            cropped0 = frame[x:x + height, y:y + width]
            cropped1 = frame[x+height:x + height * 2, y:y + width]

            # Save to file
            output_movie0.write(cropped0)
            output_movie1.write(cropped1)

            # Display the resulting frame - trying to move window, but does not always work
            cv2.namedWindow('producing video', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('producing video', cropped0.shape[1], cropped0.shape[0])
            x_pos = round(width / 2) - round(cropped0.shape[1] / 2)
            y_pos = round(height / 2) - round(cropped0.shape[0] / 2)
            cv2.moveWindow("producing video", x_pos, y_pos)
            cv2.imshow('producing video', cropped0)


            logger.info(f"Exporting videos... [frame {curr_frame}/{n_frames}]")

            # Press Q on keyboard to stop recording early
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break

    # Close video capture
    cap.release()
    # Closes the video writer.
    output_movie0.release()
    output_movie1.release()

    # Make sure all windows are closed
    cv2.destroyAllWindows()

    logger.info('Video split!')
