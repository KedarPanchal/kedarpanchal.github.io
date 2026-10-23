import yaml
from typing import Optional, Self


class DataTree:
    def __init__(self, value: Optional[str]):
        self._value = value
        self._children = []
        self._key_index_map = {}
        
    def add_child(self, key: Optional[str], value: Optional[str]) -> Self:
        self._children.append(DataTree(value))
        if key is not None:
            self._key_index_map[key] = len(self._children) - 1

        return self._children[-1]
    
    def get_child(self, index: int) -> Self:
        return self._children[index]
    
    def get_child_by_key(self, key: str) -> Self:
        return self._children[self._key_index_map[key]]
    
    def _pretty_print(self, depth: int):
        result = ('\t' * depth) + str(self._value) + '\n'
        for c in self._children:
            result += c._pretty_print(depth + 1)
        return result
    
    def __str__(self):
        return self._pretty_print(0)


class YAMLParser:
    def __init__(self, data_path: str):
        self._data_tree = DataTree(None)
        data_dict = self._load_dict(data_path)
        self._build_tree(self._data_tree, data_dict)

    def _load_dict(self, path: str) -> dict:
        with open(path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)

    def _add_tree_child(self, root: DataTree, key: Optional[str], value: str | dict | list):
        if isinstance(value, dict) or isinstance(value, list):
            # assert key is not None, f"Assertion failed on node: {root._value}"
            child = root.add_child(key, key)
            return self._build_tree(child, value)
        else:
            root.add_child(key, value)

    def _build_tree(self, root: DataTree, data: dict | list) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                self._add_tree_child(root, key, value)
        else:
            for element in data:
                self._add_tree_child(root, None, element)
