import yaml
import config as cfg

with open('messages.yml', 'r', encoding="utf-8") as f:
    msg = yaml.safe_load(f)

if cfg.LANGUAGE != 'en':
    with open(f'messages_{cfg.LANGUAGE}.yml', 'r', encoding="utf-8") as f:
        msg.update(yaml.safe_load(f))