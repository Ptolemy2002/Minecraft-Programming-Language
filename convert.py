import json
import csv
import main
import os

def start():
  files = []
  files.extend([os.path.join(".saved/tags/blocks", f) for f in os.listdir(".saved/tags/blocks") if os.path.isfile(os.path.join(".saved/tags/blocks", f))])
  files.extend([os.path.join(".saved/tags/entity_types", f) for f in os.listdir(".saved/tags/entity_types") if os.path.isfile(os.path.join(".saved/tags/entity_types", f))])
  files.extend([os.path.join(".saved/tags/items", f) for f in os.listdir(".saved/tags/items") if os.path.isfile(os.path.join(".saved/tags/items", f))])
  files.extend([os.path.join(".saved/tags/liquids", f) for f in os.listdir(".saved/tags/liquids") if os.path.isfile(os.path.join(".saved/tags/liquids", f))])

  for f in files:
    sp = f.split("/")
    if main.segment("minecraft:", 0, sp[-1]):
      split = f.split(":")
      if not split[1].endswith(".txt"):
        os.rename(f, f"{'/'.join(sp[:-1])}/minecraft_{split[1]}.txt")
      else:
        os.rename(f, f"{'/'.join(sp[:-1])}/minecraft_{split[1]}")
