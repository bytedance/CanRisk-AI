# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT
import os
import cv2
import base64
import json_repair
from typing import Dict
from llm2json.output import JSONParser


def json_parse(text: str) -> Dict:
    text = text.replace('$', '').replace('\\', '')
    try:
        parser = JSONParser()
        info_dict = parser.to_dict(text)
        assert isinstance(info_dict, dict)
        return info_dict
    except:
        try:
            info_dict = json_repair.repair_json(text, ensure_ascii=False)
            info_dict = json_repair.loads(info_dict)
            assert isinstance(info_dict, dict)
            return info_dict
        except:
            print('Can not parse basic information.')
            return {}


class FileInfoCollector:
    def __init__(self, directory):
        """
        Initialize the FileInfoCollector class, which takes an input directory as input.
        :param directory: the directory path where files are to be found
        """
        self.directory = directory.rstrip('/')
        self.base_name = os.path.basename(self.directory)
        self.base_path = os.path.join(self.directory, 'auto')
        self.md_files = os.path.join(self.base_path, f'{self.base_name}.md')
        self.json_files = os.path.join(self.base_path, f'{self.base_name}_middle.json')
        self.image_path = os.path.join(self.base_path, 'images')
        self._collect_files()

    def _collect_files(self):
        """
        Traverse the specified directory, find all Markdown and JSON files, and store their paths and base names in the corresponding lists.
        """
        assert os.path.isfile(self.md_files)
        assert os.path.exists(self.json_files)
        assert os.path.exists(self.image_path)


def merge_chunks(strings, min_length=500, max_length=1200):
    """
    Merge the elements in the list of strings, ensuring that the sum of the lengths of any two adjacent elements is not less than 1200.
    Parameters:
        strings (list): A list containing strings.
    Returns:
        list: The merged list of strings.
    """
    if not strings:
        return []

    result = []
    current_string = ""

    for string in strings:
        if len(string) < min_length:
            if len(current_string) + len(string) < max_length:
                current_string += "\n" + string if current_string else string
            else:
                result.append(current_string)
                current_string = string
        else:
            if current_string:
                result.append(current_string)
                current_string = ""
            result.append(string)

    if current_string:
        result.append(current_string)

    while len(result) > 1:
        merged = False
        for i in range(len(result) - 1):
            if len(result[i]) + len(result[i + 1]) < max_length:
                result[i] += "\n" + result[i + 1]
                del result[i + 1]
                merged = True
                break
        if not merged:
            break

    return result


def get_image_pixel_size(image_path):
    """
    Use the cv2 module to read the image at the specified path and return its pixel dimensions.
    :param image_path: the file path of the image
    :return: a tuple (height, width, channels) containing the image's height, width, and number of channels
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片 '{image_path}'，可能文件不存在或格式不支持。")
        height, width, channels = img.shape
        return height, width, channels
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"读取图片时发生异常: {e}")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
