from custom_path import DATA_PATH, CHAT_PATH
from utill import get_files_with_dir_path, try_except
from typing import List, Dict, Callable
from collections import OrderedDict
import csv
import os


class ChatDataLoader:

    def __init__(self, path: str, label_dict: Dict[str, str]):
        """
        :param path: path of chat file
        :param label_dict: str -> str
            e.g. {
                'ranking_point_diff': '248',
                'winner': 'BEL',
                'main': 'BEL',
                'country_1': 'BEL',
                'country_2': 'ENG'
            }

        Attributes:
            lines (List[OrderedDict])
                e.g. [
                    OrderedDict([
                        ('time_stamp', '0:00'),
                        ('author_name', 'NOL OTR'),
                        ('message', 'Hey FIFA !'),
                        ...
                    ]),
                ]
        """
        self.label_dict: dict = label_dict
        self.lines: List[OrderedDict] = list(csv.DictReader(open(path, 'r', encoding='utf-8')))

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, idx):
        return self.lines[idx]

    def __str__(self):
        return ' '.join([self.__class__.__name__, str(self.label_dict)])

    def add_feature(self, feature_name: str, feature_func: Callable, args: tuple = tuple()):
        """
        :param feature_name: str to add
        :param feature_func: def func(line: OrderedDict, args): ...
        :param args: tuple
        :return: None
        """
        new_lines: List[OrderedDict] = []
        for line in self.lines:
            line[feature_name] = feature_func(line, *args)
            new_lines.append(line)
        self.lines = new_lines
        print('Add feature: {}, {}'.format(feature_name, str(self.label_dict)))

    @try_except
    def get_label(self, key):
        return self.label_dict[key]

    @try_except
    def get_list_of_keys(self, keys: list):
        return [[line[k] for k in keys] for line in self.lines]


class MultiChatDataLoader:

    def __init__(self, path: str, loader_nums: int = None,
                 label_condition_func: Callable = None, label_condition_args: tuple = tuple()):
        """
        :param path: path of description file
        :param loader_nums: the number of loaders
        :param label_condition_func: def func(line_dict, *args): ...
        :param label_condition_args: tuple
        """
        self.chat_data_loader_list: List[ChatDataLoader] = []

        if label_condition_func:
            line_dict_list = [line_dict for line_dict in csv.DictReader(open(path, 'r', encoding='utf-8'))
                              if label_condition_func(line_dict, *label_condition_args)]
        else:
            line_dict_list = list(csv.DictReader(open(path, 'r', encoding='utf-8')))

        for i, line_dict in enumerate(line_dict_list):

            if loader_nums and i >= loader_nums:
                break

            self.chat_data_loader_list.append(ChatDataLoader(
                path=os.path.join(CHAT_PATH, line_dict.pop('file_name')),
                label_dict=dict(line_dict),
            ))

    def add_feature(self, feature_name: str, feature_func: Callable, args: tuple = tuple()):
        """
        :param feature_name: str to add
        :param feature_func: def func(line: OrderedDict, args): ...
        :param args: tuple
        :return: None
        """
        for _chat_data_loader in self.chat_data_loader_list:
            _chat_data_loader.add_feature(feature_name, feature_func, args)

    def __len__(self):
        return len(self.chat_data_loader_list)

    def __getitem__(self, target_label_dict: dict) -> List[ChatDataLoader]:
        r = []
        for _chat_data_loader in self.chat_data_loader_list:
            for label_key, label_value in target_label_dict.items():
                if _chat_data_loader.get_label(label_key) != label_value:
                    break
            else:
                r.append(_chat_data_loader)
        return r

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index >= len(self):
            raise StopIteration
        n = self.chat_data_loader_list[self.index]
        self.index += 1
        return n


if __name__ == '__main__':
    description_files = get_files_with_dir_path(DATA_PATH, 'Description')
    multi_chat_data_loader = MultiChatDataLoader(path=description_files[0], loader_nums=10)
    for chat_data_loader in multi_chat_data_loader:
        print(chat_data_loader)
