import yaml
from typing import Any, Optional, Self
from types import SimpleNamespace


class DataTree:
    def __init__(self, value: Optional[str]):
        self._value = value
        self._children = []
        self._keys = []
        self._key_index_map = {}
        
    def add_child(self, key: Optional[str], value: Optional[str]) -> Self:
        self._children.append(DataTree(value))
        self._keys.append(key)
        if key is not None:
            self._key_index_map[key] = len(self._children) - 1

        return self._children[-1]
    
    def emplace_child(self, key: Optional[str], child: Self) -> None:
        self._children.append(child)
        self._keys.append(key)
        if key is not None:
            self._key_index_map[key] = len(self._children) - 1
    
    def get_child(self, index: int) -> Optional[Self]:
        if index >= len(self._children):
            return None

        return self._children[index]
    
    def get_child_by_key(self, key: str) -> Optional[Self]:
        if key not in self._key_index_map:
            return None
        return self._children[self._key_index_map[key]]

    def get_key_by_index(self, index: int) -> Optional[str]:
        return self._keys[index]

    def get_index_by_key(self, key: str) -> Optional[int]:
        return self._key_index_map.get(key, None)

    def remove_children(self, *args: int) -> None:
        new_children = []
        new_keys = []
        new_key_index_map = {}

        for i, child in enumerate(self._children):
            if i in args:
                continue
            new_children.append(child)
            new_keys.append(self._keys[i])
            if self._keys[i] is not None:
                new_key_index_map[self._keys[i]] = i

        self._children = new_children
        self._keys = new_keys
        self._key_index_map = new_key_index_map

    def children(self) -> list[Self]:
        return self._children

    def num_children(self) -> int:
        return len(self._children)

    def value(self) -> Optional[str]:
        return self._value

    def copy(self) -> Self:
        result = DataTree(self._value)
        for i, child in enumerate(self._children):
            result.emplace_child(self.get_key_by_index(i), child.copy())
        return result  # type: ignore
    
    def to_namespace(self) -> Optional[str] | list[str] | SimpleNamespace:
        # No children means this is a leaf node, so we return the value directly
        if not self._children:
            return self._value
        
        # If all keys are None, then this node was a list in the data YAML
        if all(key is None for key in self._keys):
            return [child.to_namespace() for child in self._children]

        return SimpleNamespace(**{
            key.replace("-", "_"): child.to_namespace()
            for key, child in zip(self._keys, self._children)
            if key is not None
        })

    def _pretty_print(self, depth: int):
        result = f"{'\t' * depth}{self._value}\n"
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
    
    def _handle_include(self, data_root: DataTree, filter_root: DataTree, key: str, value: dict):
        data_child = data_root.get_child_by_key(key)
        if data_child is None:
            raise KeyError(f"{key} is an invalid key")

        if value is None or "include" not in value or value["include"] is None or value["include"] == "all":
            filter_root.emplace_child(key, data_child.copy())
        else:
            filter_child = filter_root.add_child(key, key)
            for element in value["include"]:
                assert isinstance(element, str) or isinstance(element, int) or isinstance(element, dict)

                if isinstance(element, str):
                    data_grandchild = data_child.get_child_by_key(element)
                    if data_grandchild is None:
                        raise KeyError(f"{element} is an invalid key")

                    filter_child.emplace_child(element, data_grandchild.copy())
                elif isinstance(element, int):
                    data_grandchild = data_child.get_child(element)
                    if data_grandchild is None:
                        raise KeyError(f"{element} is an invalid key")

                    filter_child.emplace_child(
                        data_child.get_key_by_index(element),
                        data_grandchild.copy()
                    )
                else:
                    self._build_filter_tree(data_child, filter_child, element)

    def _handle_exclude(self, filter_child: DataTree, key: str, value: dict):
        if value is None or "exclude" not in value:
            return

        to_remove_indices = []
        for element in value["exclude"]:
            assert isinstance(element, str) or isinstance(element, int)
            if isinstance(element, str):
                to_remove_indices.append(filter_child.get_index_by_key(element))
            else:
                to_remove_indices.append(element)

        filter_child.remove_children(*to_remove_indices)

    def _build_filter_tree(self, data_root: DataTree, filter_root: DataTree, filter_data: dict):
        for key, value in filter_data.items():
            self._handle_include(data_root, filter_root, key, value)
            filter_child = filter_root.get_child_by_key(key)

            # Should never happen, but just in case, we check for None before proceeding
            if filter_child is None:
                raise KeyError(f"{key} is an invalid key")

            self._handle_exclude(filter_child, key, value)

    def parse_view(self, view_path: str) -> DataTree:
        view_data = self._load_dict(view_path)
        filtered_tree = DataTree(None)
        self._build_filter_tree(self._data_tree, filtered_tree, view_data)
        return filtered_tree
