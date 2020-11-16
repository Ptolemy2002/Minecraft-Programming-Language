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

  with open("tags/" + file) as data:
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

  def getOption(options,x):
    split = x.split(":")
    for i in options:
      if i["namespace"] == split[0] and i["name"] == split[1]:
        return i
    return None

  print("filtering entries")
  for line in code[1:]:
    line = line.strip()
    if line[0] == "+" or line[0] == "-":
      workingString = line[1:].strip()
      workingList = []
      if workingString == "all":
        for i in options:
          workingList.append(i["namespace"] + ":" + i["nam+-e"])
      elif main.segment("all", 0, workingString):
        argString = main.groups(workingString, [["(",")"]], False)[0]
        if argString[0] == "#":
          if os.path.exists(f"tags/{argString[1:]}.mctag"):
            if not (f"{argString[1:]}.mctag" in done):
              with open(f"tags/{argString[1:]}.mctag", "r") as data:
                print(f'file "{argString[1:]}.mctag" must be loaded before continuing.')
                workingList.extend(genTag(f"{argString[1:]}.mctag", packName, packId))
                print(f'continuing to load "{file}"')
            else:
              with open(f".saved/tags/{t}/{argString[1:]}.txt", "r") as data:
                for i in data:
                  for i2 in i.split(","):
                    i2 = i2.strip()
                    if not ":" in i2:
                      workingList.append("minecraft:" + i2)
                    else:
                      workingList.append(i2)
          elif os.path.exists(f".saved/tags/{t}/{argString[1:]}.txt"):
            with open(f".saved/tags/{t}/{argString[1:]}.txt", "r") as data:
                for i in data:
                  for i2 in i.split(","):
                    i2 = i2.strip()
                    if not ":" in i2:
                      workingList.append("minecraft:" + i2)
                    else:
                      workingList.append(i2)
          else:
            #The tag isn't defined here. Append it to the pack anyway in case it's defined somewhere else.
            workingList.append(argString)
        elif "=" in argString or "<" in argString or ">" in argString:
          args = main.words(",", argString, [['"','"']], False, False)
          pars = {}
          li = []
          opCount = 0

          for arg in args:
            match = re.match(r"^(?P<key>.+)(?P<operation>\>=|\<=|!=|==|\>|\<)(?P<value>.+)$", arg)
            if not match == None:
              opCount += 1
              operation = match.group("operation")
              key = match.group("key")
              value = match.group("value")
              if operation == "==":
                for i in options:
                  if i[key] == value:
                    li.append(i["namespace"] + ":" + i["name"])
                  else:
                    li.remove(i["namespace"] + ":" + i["name"])
              elif operation == "!=":
                for i in options:
                  if not i[key] == value:
                    li.append(i["namespace"] + ":" + i["name"])
                  elif (i["namespace"] + ":" + i["name"]) in li:
                    li.remove(i["namespace"] + ":" + i["name"])
              elif operation == ">":
                value = numberCast(value)
                for i in options:
                  if numberCast(i[key]) > value:
                    li.append(i["namespace"] + ":" + i["name"])
                  elif (i["namespace"] + ":" + i["name"]) in li:
                    li.remove(i["namespace"] + ":" + i["name"])
              elif operation == "<":
                value = numberCast(value)
                for i in options:
                  if numberCast(i[key]) < value:
                    li.append(i["namespace"] + ":" + i["name"])
                  elif (i["namespace"] + ":" + i["name"]) in li:
                    li.remove(i["namespace"] + ":" + i["name"])
              elif operation == ">=":
                value = numberCast(value)
                for i in options:
                  if numberCast(i[key]) >= value:
                    li.append(i["namespace"] + ":" + i["name"])
                  elif (i["namespace"] + ":" + i["name"]) in li:
                    li.remove(i["namespace"] + ":" + i["name"])
              elif operation == "<=":
                value = numberCast(value)
                for i in options:
                  if numberCast(i[key]) <= value:
                    li.append(i["namespace"] + ":" + i["name"])
                  elif (i["namespace"] + ":" + i["name"]) in li:
                    li.remove(i["namespace"] + ":" + i["name"])
            elif "=" in arg:
              par = main.words("=", arg, [['"','"']], False, False)
              if not par[0] in pars:
                pars[par[0]] = []
              pars[par[0]].append(par[1])

          if opCount == 0:
            for i in options:
              li.append(i["namespace"] + ":" + i["name"])

          if "sort" in pars:
            if pars["sort"][-1] == "alphabetical":
              li = sorted(li)
              pass
            else:
              def value(li1):
                def inner(x):
                  split = x.split(":")
                  for i in li1:
                    if i["namespace"] == split[0] and i["name"] == split[1]:
                      num = numberCast(i[pars["sort"][-1]])
                      if not num == -math.inf:
                        return (1,num)
                      else:
                        return (2,i[pars["sort"][-1]])
                  return (0,x)
                return inner
              
              li = sorted(li, key=value(options))

          if "reverse" in pars:
            if pars["reverse"][-1].lower() == "true":
              li.reverse()

          if "limit" in pars:
            li = li[:min(len(li),int(numberCast(pars["limit"][-1])))]
          
          if "in" in pars:
            for seg in pars["in"]:
              for i in li:
                if not seg in i:
                  li.remove(i)
          
          if "notin" in pars:
            for seg in pars["notin"]:
              for i in li:
                if seg in i:
                  li.remove(i)
          for i in li:
            workingList.append(i)
        else:
          reverse = False
          if argString[0] == "!":
            argString = argString[1:]
            reverse = True
          else:
            reverse = False
          
          for i in options:
              if argString in i["name"] and not reverse:
                workingList.append(i["namespace"] + ":" + i["name"])
              elif reverse and not argString in i["name"]:
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
    elif line == "reverse":
      result.reverse()
    elif main.segment("sort", 0, line):
      argString = main.groups(line, [["(",")"]], False)[0]
      if argString == "alphabetical":
        result = sorted(result)
        pass
      else:
        def value(li1):
          def inner(x):
            split = x.split(":")
            for i in li1:
              if i["namespace"] == split[0] and i["name"] == split[1]:
                num = numberCast(i[argString])
                if not num == -math.inf:
                  return (1,num)
                else:
                  return (2,i[argString])
            return (0,x)
          return inner

        result = sorted(result, key=value(options))
    elif main.segment("limit", 0, line):
      argString = main.groups(line, [["(",")"]], False)[0]
      result = result[:min(len(result),int(numberCast(argString)))]

  name_split = name.split("/")
  
  if len(name_split) > 1:
    os.makedirs(f".generated/packs/{packName}/data/{packId}/tags/{t}/{'/'.join(name_split[:len(name_split)-1])}", exist_ok=True)
  with open(f".generated/packs/{packName}/data/{packId}/tags/{t}/{name}.json", "w+") as file1:
    json.dump({"replace": False, "values":result}, file1,indent=4)

  if len(name_split) > 1:
    os.makedirs(f".saved/tags/{t}/{'/'.join(name_split[:len(name_split)-1])}", exist_ok=True)
    print(f".saved/tags/{t}/{'/'.join(name_split[:len(name_split)-1])}")
  with open(f".saved/tags/{t}/{name}.txt", "w+") as data:
    data.write("\n".join(result))

  print(f'done loading "{file}"')
  print(f'deleting "{t}.csv" from memory to save space')
  del options

  done.append(file)
  return result

def start(packName, packId, packDesc):
  print("Creating necessary file paths")
  os.makedirs("tags", exist_ok=True)
  os.makedirs(".saved/tags/blocks", exist_ok = True)
  os.makedirs(".saved/tags/entity_types", exist_ok = True)
  os.makedirs(".saved/tags/items", exist_ok = True)
  os.makedirs(".saved/tags/functions", exist_ok = True)

  print("looking for mctag files")
  for subdir, dirs, files in os.walk(os.getcwd() + "/tags"):
    dirs[:] = [d for d in dirs if not d[0] == "."]
    for file in files:
      path = os.path.relpath(os.path.join(subdir, file))
      if file.endswith(".mctag") and not path[path.index("/") + 1:] in done:
        genTag(path[path.index("/") + 1:], packName, packId)
      
if __name__ == "__main__":
  start(main.packName, main.packId, main.packDesc)