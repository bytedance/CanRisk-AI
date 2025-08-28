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
        初始化 FileInfoCollector 类，接收输入目录作为输入。
        :param directory: 要查找文件的目录路径
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
        遍历指定目录，查找所有的 Markdown 和 JSON 文件，并将它们的路径和基本名称存储在相应的列表中。
        """
        assert os.path.isfile(self.md_files)
        assert os.path.exists(self.json_files)
        assert os.path.exists(self.image_path)


def merge_chunks(strings, min_length=500, max_length=1200):
    """
    合并字符串列表中的元素，确保任意相邻两个元素的长度和不小于1200。
    参数：
        strings (list): 包含字符串的列表。
    返回：
        list: 合并后的字符串列表。
    """
    # 检查输入是否为空
    if not strings:
        return []

    # 初始化结果列表
    result = []

    # 初始化当前合并字符串
    current_string = ""

    for string in strings:
        # 检查当前字符串长度是否小于500
        if len(string) < min_length:
            # 尝试合并到当前字符串
            if len(current_string) + len(string) < max_length:
                current_string += "\n" + string if current_string else string
            else:
                # 当前字符串长度已经达到要求，保存并重置
                result.append(current_string)
                current_string = string
        else:
            # 当前字符串长度>=500，先保存当前字符串
            if current_string:
                result.append(current_string)
                current_string = ""
            result.append(string)

    # 最后检查是否有未保存的字符串
    if current_string:
        result.append(current_string)

    # 确保所有相邻元素满足要求
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
    使用 cv2 模块读取指定路径的图片，并返回其像素尺寸。
    :param image_path: 图片的文件路径
    :return: 一个包含图片高度、宽度和通道数的元组 (height, width, channels)
    """
    try:
        # 使用 cv2 读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"无法读取图片 '{image_path}'，可能文件不存在或格式不支持。")
        # 获取图片的高度、宽度和通道数
        height, width, channels = img.shape
        return height, width, channels
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"读取图片时发生异常: {e}")


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
