import os
import json
import tags
import convert

"""
Given a list of lists (or ranges) [li], return if [x] is included in any of them
"""
def inAny(x, li):
  for i in li:
    if x in i:
      return True

  return False

def segment(s, i, string):
  for ind in range(0,len(s)):
    if not s[ind] == string[ind + i]:
      return False

  return True

"""
A method used in parsing to determine which indexes that are surrounded in a given list of value pairs.
For example, if the ignoreChars value was [["(",")"]] and the string was "(hello (guys)) (hi)", this method
would identify the range including "(hello (guys))", enabling methods to consider that one element rather than
multiple.

Each item in the ignoreChars parameter is a pair of start and end values. Defining multiple items will add alternative
pairs. You may optionally provide a third argument that is a boolean defining whether the pair characters may be escaped.
"""
def ignoreIndexes(string, ignoreChars, inclusive):
  altInds = []
  if (len(ignoreChars) > 1):
    for i in ignoreChars:
      altInds.extend(ignoreIndexes(string, [i], False))

  result = []
  ignore = False
  ignoreCount = 0
  ignoreList = None
  startIndex = -1

  for i in range(0,len(string)):
    if (not ignoreList == None) and len(ignoreList) > 2 and ignoreList[2] == True and i > 0 and (string[i - 1] == "\\" and not string[i - 2] == "\\"):
      #The character is escaped. Continue as if it wasn't there.
      continue
    
    c = string[i]

    if not ignore:
      for l in ignoreChars:
        if c == l[0] and not inAny(i, altInds):
          ignoreList = l
          ignoreCount += 1
          ignore = True
          startIndex = i
    elif not ignoreList[0] == ignoreList[1]:
      if ignoreList[0] == c and not inAny(i, altInds):
        ignoreCount += 1
      
      if ignoreList[1] == c and not inAny(i, altInds):
        ignoreCount -= 1
        if ignoreCount == 0:
          ignoreList = None
          ignore = False
          result.append(range(startIndex + int(not inclusive), i + int(inclusive)))
          startIndex = -1
    elif ignoreList[1] == c and not inAny(i, altInds):
      ignoreCount = 0
      ignoreList = None
      ignore = False
      result.append(range(startIndex + int(not inclusive), i + int(inclusive)))
      startIndex = -1

  return result

"""
Get the strings associated with a specific call of ignoreIndexes
"""
def groups(string, ignoreChars, inclusive):
  result = []
  indexes = ignoreIndexes(string, ignoreChars, inclusive)
  for r in indexes:
    result.append(string[r[0]:r[-1] + 1])
  return result

"""
Return the first appearance of {character} in {string} that is not part of a group defined by {ignoreChars}
(see ignoreIndexes)
"""
def indexOf(character, string, ignoreChars):
  ignoreInds = ignoreIndexes(string, ignoreChars, True)

  for i in range(0,len(string)):
    c = string[i]
    if (not inAny(i, ignoreInds)) and c == character:
      return i

  #No match was found
  return -1

"""
Takes a list of file lines as {data} and removes any comments. That is, any lines
that start with "#" and any characters that trail after "#" at the end of a line.
"""
def noComments(data):
  result = []

  for l in data:
    line = l.strip()
    hashtagIndex = indexOf("#", line, [["\"", "\""], ["[", "]"], ["/", ";"], ["(", ")"]])
    if hashtagIndex > 0:
      result.append(line[:hashtagIndex].strip())
    elif hashtagIndex != 0 and len(line) > 0:
      result.append(line)
  
  return result

"""
Return a list of elements separated by {separator} in {string}, grouping using the {ignoreChars}
(see ignoreIndexes)
"""
def words(separator, string, ignoreChars, separatorInclusive, ignoreCharInclusive):
  result = [""]
  ignoreInds = ignoreIndexes(string, ignoreChars, True)

  for i in range(0, len(string)):
    if (not inAny(i, ignoreInds)) and string[i] == separator:
      if separatorInclusive:
        result[-1] += string[i]
      result.append("")
    elif ignoreCharInclusive or not (i >= 2 and inAny(string[i], ignoreChars) and not (string[i - 1] == "\\" and not string[i - 2] == "\\")):
      result[-1] += string[i]

  if result[-1] == "":
    result = result[:len(result) - 1]

  return result

class Statement:
  def __init__(self, text, parentFunction):
    self.text = text
    self.parentFunction = parentFunction
  
  def implement(self):
    self.parentFunction.append(self.text)

class Comment(Statement):
  def implement(self):
    self.parentFunction.append("#" + self.text)

class Function:
  def __init__(self, name, desc):
    self.name = name
    self.code = []
    Comment(desc, self).implement()
  
  def append(self, value):
    self.code.append(value)
  
  def implement(self, filePath):
    with open(filePath, "w+") as file:
      file.write("\n".join(self.code))

packName = "Generated Data Pack"
packId = "generated_data_pack"
packDesc = "Data pack generated from a Minecraft Programming Language compiler"
defaultPackInfo = False

initFunction = Function("load", "This function is run when the datapack is loaded.")
uninstallFunction = Function("uninstall", "Can be called to remove the pack and any trace it was ever installed")
tickFunction = Function("tick", "This function is run every tick after this datapack is loaded.")
customFunctions = {"test": Function("test", "this is a test.")}

def generateCode(code):
  #TODO: Convert each line of code to an instance of Statement or Variable that can then be converted to datapack form.
  pass

def main():
  print("Start")

  mainCode = []
  with open("main.mcscript", "r") as data:
    print("found main file")
    codeList = noComments(data)
    #A list of each separate statement or definition without any new lines or tabs
    mainCode = words(";", "".join(codeList), [["\"", "\"", True], ["{", "}"]], False, True)
  
  """print("main file contents:")
  for i in range(0,len(mainCode)):
    print(f"\t{i}: {mainCode[i]}")"""

  if segment("pack-info: ", 0, mainCode[0]):
    info = packId = words(" ", mainCode[0], [['"', '"', True]], False, False)[1:]
    packName = info[0]
    packId = info[1]
    packDesc = info[2]
    defaultPackInfo = False
    print(f'got pack name "{packName}" with id "{packId}"')
    print("Converting to data pack form")
  else:
    print(f'no pack info specified. Default values will be used (name "{packName}" id {packId})')
    defaultPackInfo = True
  
  print("Populating default function statements")

  print("Converting main file to datapack form")
  if defaultPackInfo:
    generateCode(mainCode[1:])
  else:
    generateCode(mainCode)

  print("looking for other files")
  for subdir, dirs, files in os.walk(os.getcwd()):
    for file in files:
      if file.endswith(".mcscript") and not file == "main.mcscript":
        path = os.path.join(subdir, file).split("/")
        path = "/".join(path[path.index("Minecraft-Programming-Language") + 1:])
        print(f"found file \"{path}\"")
        with open(path) as data:
          print("Converting to data pack form")
          generateCode(words(";", "".join(noComments(data)), [["\"", "\"", True], ["{", "}"]], False, True))

  print('Adding "datapack loaded/unloaded" notification')
  initFunction.append(f'tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully (re)loaded."}}]')
  uninstallFunction.append(f'tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully unloaded."}}]')

  print("Saving functions for use in tags")
  with open(".saved/data/functions.csv", "w+") as file:
    data = ["name","internal/load", "internal/tick", "uninstall"]
    for i in customFunctions:
      data.append(i)
    file.write("\n".join(data))
  print("Generating tag files")
  tags.start(packName, packId, packDesc)

  print("setting up data pack files")
  os.makedirs(f".generated/packs/{packName}/data/minecraft/tags/functions", exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/functions/internal', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/blocks', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/entity_types', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/fluids', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/functions', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/items', exist_ok = True)
  with open(f".generated/packs/{packName}/pack.mcmeta", "w+") as file:
    json.dump({"pack":{"pack-format":6,"description": packDesc}}, file)
  with open(f".generated/packs/{packName}/data/minecraft/tags/functions/load.json", "w+") as file:
    json.dump({"replace": False, "values":[f"{packId}:internal/{initFunction.name}"]}, file)
  with open(f".generated/packs/{packName}/data/minecraft/tags/functions/tick.json", "w+") as file:
    json.dump({"replace": False, "values":[f"{packId}:internal/{tickFunction.name}"]}, file)

  print("Writing init function to data pack")
  initFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/internal/{initFunction.name}.mcfunction")
  print("Writing uninstall function to data pack")
  uninstallFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/{uninstallFunction.name}.mcfunction")
  print("Writing tick function to data pack")
  tickFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/internal/{tickFunction.name}.mcfunction")
  for name in customFunctions:
    print(f'Writing "{name}" function to data pack')
    customFunctions[name].implement(f".generated/packs/{packName}/data/{packId}/functions/{name}.mcfunction")
  
  print("Done")

if __name__ == "__main__":
  main()
  #tags.start()
  #convert.start()
  #regex_test.start()