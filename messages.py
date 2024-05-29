import yaml
import config as cfg

with open(cfg.RESOURCES/'messages.yml', 'r', encoding="utf-8") as f:
    msg = yaml.safe_load(f)

if cfg.LANGUAGE != 'en':
    lang_file = cfg.RESOURCES/f'messages_{cfg.LANGUAGE}.yml'
    with open(lang_file, 'r', encoding="utf-8") as f:
        msg.update(yaml.safe_load(f))