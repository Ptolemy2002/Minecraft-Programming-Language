import main
import csv
import os
import math
import json
import re

done = []

def numberCast(i):
  try:
    return float(i)
  except:
    return -math.inf

def genTag(file, packName, packId):
  print(f'loading file "{file}"')
  name = file[:file.index(".mctag")]
  result = []
  code = []
  options = []

  with open(file) as data:
    for i in data:
      code.append(i)
  
  #print("contents:")
  code = main.noComments(code)
  for i in range(0,len(code)):
    code[i] = code[i].replace(" ", "")
    #print(f"\t{i}: {code[i]}")

  t = main.words(":", code[0], [['"','"']], False, False)[1]
  print(f'type is "{t}"')
  print(f'Loading "{t}.csv" into memory')

  with open(f".saved/data/{t}.csv", "r") as csvFile:
    dictReader = csv.DictReader(csvFile)
    for i in dictReader:
      options.append(i)

  print(f'got {len(options)} entries from "{t}.csv"')

  print("filtering entries")
  for line in code[1:]:
        workingString = line[1:].strip()
        workingList = []
        if workingString == "all":
          for i in options:
            workingList.append(i["namespace"] + ":" + i["name"])
        elif main.segment("all", 0, workingString):
          argString = main.groups(workingString, [["(",")"]], False)[0]
          if argString[0] == "#":
            if os.path.exists(f"{argString[1:]}.mctag"):
              if not (f"{argString[1:]}.mctag" in done):
                with open(f"{argString[1:]}.mctag", "r") as data:
                  print(f'file "{argString[1:]}.mctag" must be loaded before continuing.')
                  workingList.extend(genTag(f"{argString[1:]}.mctag", packName, packId))
                  print(f'continuing to load "{file}"')
              else:
                with open(f".saved/tags/{t}/{argString[1:]}.txt", "r") as data:
                  for i in data:
                    workingList.append(i)
            elif os.path.exists(f".saved/tags/{t}/{argString[1:]}.txt"):
              with open(f".saved/tags/{t}/{argString[1:]}.txt", "r") as data:
                for i in data:
                  workingList.append(i)
            else:
              #The tag isn't defined here. Append it to the pack anyway in case it's defined somewhere else.
              workingList.append(argString)
          elif "=" in argString or "<" in argString or ">" in argString:
            match = re.match(r"^(?P<key>.+)(?P<operation>\>=|\<=|!=|==|\>|\<)(?P<value>.+)$", argString)
            operation = match.group("operation")
            key = match.group("key")
            value = match.group("value")
            if operation == "==":
              for i in options:
                if i[key] == value:
                  workingList.append(i["namespace"] + ":" + i["name"])
            elif operation == "!=":
              for i in options:
                if not i[key] == value:
                  workingList.append(i["namespace"] + ":" + i["name"])
            elif operation == ">":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) > value:
                  workingList.append(i["namespace"] + ":" + i["name"])
            elif operation == "<":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) < value:
                  workingList.append(i["namespace"] + ":" + i["name"])
            elif operation == ">=":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) >= value:
                  workingList.append(i["namespace"] + ":" + i["name"])
            elif operation == "<=":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) <= value:
                  workingList.append(i["namespace"] + ":" + i["name"])
          else:
            for i in options:
                if argString in i["name"]:
                  workingList.append(i["namespace"] + ":" + i["name"])
            
        elif ":" in workingString:
          workingList.append(workingString)
        else:
          workingList.append("minecraft:" + workingString)

        if line[0] == "+":
          for i in workingList:
            if not i.strip() in result:
              result.append(i.strip())
        elif line[0] == "-":
          for i in workingList:
            element = i.strip()
            if element in result:
              result.remove(element)

  name_split = name.split("/")
  if len(name_split) > 1:
    os.makedirs(f".generated/packs/{packName}/data/{packId}/tags/{t}/{name_split[:len(name_split)-1][0]}", exist_ok=True)
  with open(f".generated/packs/{packName}/data/{packId}/tags/{t}/{name}.json", "w+") as file1:
    json.dump({"replace": False, "values":result}, file1,indent=4)

  if len(name_split) > 1:
    os.makedirs(f".saved/tags/{t}/{name_split[:len(name_split)-1][0]}", exist_ok=True)
  with open(f".saved/tags/{t}/{name}.txt", "w+") as data:
    data.write("\n".join(result))

  print(f'done loading "{file}"')
  print(f'deleting "{t}.csv" from memory to save space')
  del options

  done.append(file)
  return result

def start(packName, packId, packDesc):
  print("Creating necessary file paths")
  os.makedirs(".saved/tags/blocks", exist_ok = True)
  os.makedirs(".saved/tags/entity_types", exist_ok = True)
  os.makedirs(".saved/tags/items", exist_ok = True)
  os.makedirs(".saved/tags/functions", exist_ok = True)

  print("looking for mctag files")
  for subdir, dirs, files in os.walk(os.getcwd()):
    dirs[:] = [d for d in dirs if not d[0] == "."]
    for file in files:
      path = os.path.join(subdir, file).split("/")
      path = "/".join(path[path.index("Minecraft-Programming-Language") + 1:])
      if file.endswith(".mctag") and not path in done:
        genTag(path, packName, packId)
      
if __name__ == "__main__":
  start(main.packName, main.packId, main.packDesc)