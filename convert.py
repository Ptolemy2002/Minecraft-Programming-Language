import json
import main

def start():
  with open("blocks.json", "r") as file:
    data = json.load(file)
    newFile = ["namespace,name"]
    for i in data:
      words = main.words(":", i, [], False, False)
      newFile.append(f"{words[0]},{words[1]}")
      print(f"{words[0]},{words[1]}")
    
    with open("saved/data/blocks.csv", "w+") as file1:
      file1.write("\n".join(newFile))