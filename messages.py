import yaml

with open('messages.yml', 'r', encoding="utf-8") as f:
    msg = yaml.safe_load(f)

# with open('messages_de.yml', 'r', encoding="utf-8") as f:
#     msg.update(yaml.safe_load(f))