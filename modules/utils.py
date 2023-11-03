import json
from base64 import b64decode, b64encode
import re
import logging

from argparse import ArgumentParser
from string import Template

import os
package_directory = os.path.dirname(os.path.abspath(__file__))
print('package_directory', __name__, package_directory)

arg_parser = ArgumentParser()


def get_decode(string) -> str:
    return b64decode(string).decode("utf-8")

def get_encode(string) -> str:
    return b64encode(string.encode("utf-8"))

def load_config(path: str = None, key: str = None, env_key: str = None) -> dict:

    if env_key == None:
        env_key = "CONFIG_FILE"
    
    if path == None:
        env_path = os.environ.get(env_key)
        if env_path == None :
            env_path = "config.json"
            logging.error(f"Key {env_key} not found in environment")
        path = f'{package_directory}/../{env_path}'

    # Загрузка файла конфига
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if key == None:
        return config
    else:
        keyed_config = config.get(key)
        if keyed_config:
            return keyed_config
        else:
            raise ConfigError (f"Not found '{key}' key in config")

def save_config(config, path: str = None) -> dict:
    
    if path == None:
        path = f'{package_directory}/../{os.environ.get("CONFIG_FILE", "config.json")}'

    # Сохранение файла конфига
    with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    return config

def escape_text(text) -> str:
    regex = r"([_*[\]()~`>#+\-=|{}.!])"
    subst = "\\\\\\1"
    result = re.sub(regex, subst, text, 0)
    return result

class ConfigError(Exception):
    pass

class JsonTemplate(Template):

    def substitute(self, mapping: dict):
        # Helper function for .sub()
        def convert(mo):
            name = mo.group('braced')
            return_str = json.dumps(mapping[name], ensure_ascii=False)[1:-1]
            return return_str

        return self.pattern.sub(convert, self.template)
    