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

  with open(f"saved/data/{t}.csv", "r") as csvFile:
    dictReader = csv.DictReader(csvFile)
    for i in dictReader:
      options.append(i)

  print(f'got {len(options)} entries from "{t}.csv"')

  for line in code[1:]:
        workingString = line[1:]
        workingList = []

        if main.segment("all", 0, workingString):
          argString = main.groups(workingString, [["(",")"]], False)[0]
          if argString[0] == "#":
            if os.path.exists(f"{argString[1:]}.mctag"):
              if not (f"{argString[1:]}.mctag" in done):
                with open(f"{argString[1:]}.mctag", "r") as data:
                  print(f'file "{argString[1:]}.mctag" must be loaded before continuing.')
                  workingList.extend(genTag(f"{argString[1:]}.mctag", packName, packId))
              else:
                with open(f"saved/tags/{t}/{argString[1:]}.txt", "r") as data:
                  for i in data:
                    workingList.append(i)
            elif os.path.exists(f"saved/tags/{argString[1:]}.txt"):
              with open(f"saved/tags/{argString[1:]}.txt", "r") as data:
                for i in data:
                  workingList.append(i)
          else:
            match = re.match(r"^(?P<key>.+)(?P<operation>\>=|\<=|!=|==|\>|\<)(?P<value>.+)$", argString)
            operation = match.group("operation")
            key = match.group("key")
            value = match.group("value")
            if operation == "==":
              for i in options:
                if i[key] == value:
                  workingList.append("minecraft:" + i["name"])
            elif operation == "!=":
              for i in options:
                if not i[key] == value:
                  workingList.append("minecraft:" + i["name"])
            elif operation == ">":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) > value:
                  workingList.append("minecraft:" + i["name"])
            elif operation == "<":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) < value:
                  workingList.append("minecraft:" + i["name"])
            elif operation == ">=":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) >= value:
                  workingList.append("minecraft:" + i["name"])
            elif operation == "<=":
              value = numberCast(value)
              for i in options:
                if numberCast(i[key]) <= value:
                  workingList.append("minecraft:" + i["name"])
            
        elif ":" in workingString:
          workingList.append(workingString)
        else:
          workingList.append("minecraft:" + workingString)

        if line[0] == "+":
          result.extend(workingList)
        elif line[0] == "-":
          for i in workingList:
            element = i.strip()
            if element in result:
              result.remove(element)

  with open(f"generated/packs/{packName}/data/{packId}/tags/{t}/{name}.json", "w+") as file1:
    json.dump({"replace": False, "values":result}, file1)

  with open(f"saved/tags/{t}/{name}.txt", "w+") as data:
    data.write("\n".join(result))

  print(f'deleting "{t}.csv" from memory to save space')
  del options

  done.append(file)
  return result

def start(packName, packId, packDesc):
  print("Creating necessary file paths")
  os.makedirs("saved/tags/blocks", exist_ok = True)
  os.makedirs("saved/tags/entity_types", exist_ok = True)
  os.makedirs("saved/tags/items", exist_ok = True)
  os.makedirs("saved/tags/functions", exist_ok = True)

  print("looking for mctag files")
  for file in os.listdir(os.getcwd()):
    if file.endswith(".mctag") and not file in done:
      genTag(file, packName, packId)
      
if __name__ == "__main__":
  start(main.packName, main.packId, main.packDesc)