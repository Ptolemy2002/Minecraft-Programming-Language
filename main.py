import os
import json
import tags
import shutil
import re
#import convert

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

class Variable:
  def __init__(self, namespace, name, modifier, t, value, desc, define):
    value = value.strip()

    self.namespace = namespace
    self.modifier = modifier
    self.type = t

    if segment("float", 0, self.type):
      if "[]" in self.type:
        self.type = "float[]"
      else:
        self.type = "float"
      
    self.name = name
    self.precision = None
    self.value = value
    self.desc = desc
    
    if "float" in self.type:
      match = re.match(r"float(\<(?P<precision>\d+)\>)?(\[\])?", t)
      self.precision = int(match.group("precision"))
    
    if value != None:
      if self.type == "int":
        self.value = int(self.value)
      elif self.type == "float":
        self.value = float(self.value[:-1])
      elif self.type == "string":
        self.value = groups(self.value, [['"', '"', True], ["'", "'", True]], False)[0]
      elif "[]" in self.type:
        self.value = []
        for item in value[1:-1].split(","):
          item = item.strip()
          if "int" in self.type:
            self.value.append(int(item))
          elif "float" in self.type:
            self.value.append(float(item[:-1]))
          elif "string" in self.type:
            self.value.append(groups(item, [['"', '"', True], ["'", "'", True]], False)[0])
          else:
            self.value.append(value)

    variables[self.name] = self
    if define:
      DefineVariable(self, initFunction).implement()

class DefineVariable(Statement):
  def __init__(self, variable, parentFunction):
    if variable.desc != None:
      Comment(variable.desc, parentFunction).implement()

    text = ""
    super().__init__(text, parentFunction)

class Function:
  def __init__(self, namespace, name, desc, priority):
    self.name = name
    self.path = "/".join(name.split("/")[:-1])
    self.namespace = namespace
    self.priority = priority
    if self.priority == None:
      self.priority = 0
    self.code = []
    self.listenerId = None
    self.scoreId = None
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
useSnapshots = False

initFunction = Function(packId, "internal/load", "This function is run when the datapack is loaded.", 0)
uninstallFunction = Function(packId, "uninstall", "Can be called to remove the pack and any trace it was ever installed", 0)
tickFunction = Function(packId, "internal/tick", "This function is run every tick after this datapack is loaded.", 0)
customFunctions = {}
listeners = {}
externalFunctions = []
internalListeners = ["load", "tick", "uninstall", "spawn"]
variables = {}
playerPreference = "both"

def generateCode(code, function, path, file):
  global listeners
  global externalFunctions
  global customFunctions
  global packId

  if function == None:
    #Top-level statements: Variables and function declarations
    for line in code:
      match = re.match(r'(priority\=(?P<priority>[+-]?\d+)\s+)?(id="(?P<id>[^\"]+)"\s+)?on\s+(?P<name>[a-z_0-9\.\:]+)', line)
      if match != None:
        name = match.group("name").replace(":", "_")
        id = match.group("id")
        priority = match.group("priority")
        if not name in listeners:
          listeners[name] = []
        version = len(listeners[name]) + 1
        function = None
        if priority == None:
          function = Function(packId, f"listeners/{name}/{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}{version}", f"This function is called for every {name} event with 0 priority", 0)
        else:
          priority = int(priority)
          function = Function(packId, f"listeners/{name}/{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}{version}", f"This function is called for every {name} event with {priority} priority", priority)
        
        function.listenerId = match.group("name")
        function.scoreId = name
        if id != None:
          function.scoreId = id
        statements = words(";", groups(line, [["{", "}"]], False)[0], [['"', '"', True], ["'", "'", True], ["{", "}"]], False, True)
        customFunctions[function.name] = function
        listeners[name].append(function)
        generateCode(statements, function, function.path, f"{name.replace('.', '_')}-{version}.mcscript")
      else:
        match = re.match(r'function\s+(desc="(?P<desc>[^\"]+)"\s+)?(?P<name>[a-z_]+)\(\)', line)
        if match != None:
          name = match.group("name")
          desc = match.group("desc")
          function = None
          if desc == None:
            function = Function(packId, f"{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}", f"The function defined with the name '{name}' in the file '{path}/{file}'", 0)
          else:
            function = Function(packId, f"{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}", desc, 0)
          statements = words(";", groups(line, [["{", "}"]], False)[0], [['"', '"', True], ["'", "'", True], ["{", "}"]], False, True)
          customFunctions[function.name] = function
          generateCode(statements, function, function.path, function.name)
        else:
          match  = re.match(r'def (?P<namespace>[a-z_\/]+):(?P<name>[a-z_]+)', line)
          if match != None:
            externalFunctions.append(Function(match.group("namespace"), match.group("name"), "", 0))
          else:
            match = re.match(r'(?P<modifier>global|entity|constant)\s+(desc="(?P<desc>[^\"]+)"\s+)?(?P<type>(?:entity|int|float|string|bool)(?:\<\d+\>)?(?:\[\])?)\s+(?P<name>[a-zA-Z_]+)(\s*\=\s*(?P<value>.+))?', line)
            if match != None:
              modifier = match.group("modifier")
              t = match.group("type")
              name = match.group("name")
              value = match.group("value")
              desc = match.group("desc")
              print(f'Defining variable "{name}"')
              Variable(packId, name, modifier, t, value, desc, True)
            else:
              pass
  else:
    #TODO: Convert each line of code to an instance of Statement or Variable that can then be converted to datapack form.
    pass

def main():
  global packId
  global packDesc
  global packName
  global useSnapshots
  global packDesc
  global variables
  global playerPreference

  print("Start")

  mainCode = []
  with open("main.mcscript", "r") as data:
    print("found main file")
    codeList = noComments(data)
    #A list of each separate statement or definition without any new lines or tabs
    mainCode = words(";", "".join(codeList), [['"', '"', True], ["'", "'", True], ["{", "}"]], False, True)
  
  """print("main file contents:")
  for i in range(0,len(mainCode)):
    print(f"\t{i}: {mainCode[i]}")"""

  if segment("pack-info: ", 0, mainCode[0]):
    info = packId = words(" ", mainCode[0], [['"', '"', True], ["'", "'", True]], False, False)[1:]
    packName = info[0]
    packId = info[1]
    packDesc = info[2]
    print(f'got pack name "{packName}" with id "{packId}"')
    useSnapshots = bool(info[3].lower().capitalize())
    if useSnapshots:
      print("Snapshots have been enabled. Pack format changed to 7.")
    else:
      print("No snapshots are in use. Pack format is 6.")
    playerPreference = info[4].lower()
    defaultPackInfo = False
    print("Converting to data pack form")
  else:
    print(f'no pack info specified. Default values will be used (name "{packName}" id {packId})')
    defaultPackInfo = True

  if os.path.isdir(f".generated/packs/{packName}"):
    print("Cleaning up previous generation files")
    while os.path.isdir(f".generated/packs/{packName}"):
      shutil.rmtree(f".generated/packs/{packName}")

  print("Populating default function statements")
  Statement(f"scoreboard objectives add {packId}_t dummy", initFunction).implement()
  Statement(f"scoreboard objectives remove {packId}_t", uninstallFunction).implement()
  Statement(f"scoreboard players set {packId} {packId}_t 0", initFunction).implement()
  if playerPreference == "single":
    Comment("Ensure the game is run in singleplayer", initFunction).implement()
    Statement(f"execute as @a run scoreboard players add {packId} {packId}_temp 1", initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches 2.. run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with singleplayer.\\nDisabling the pack to avoid unexpected behavior."}}]', initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches 2.. run scoreboard objectives remove {packId}_temp', initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches 2.. run datapack disable {packId}', initFunction).implement()
    Statement(f'execute store success storage {packId} isCompatible int if score {packId} {packId}_t matches ..1', initFunction).implement()
  elif playerPreference == "multi":
    Statement(f"execute as @a run scoreboard players add {packId} {packId}_temp 1", initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches ..1 run tellraw @a [{{"text":"The pack "}},{{"text":"{packName}","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with multiplayer.\\nDisabling the pack to avoid unexpected behavior."}}]', initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches ..1 run scoreboard objectives remove {packId}_temp', initFunction).implement()
    Statement(f'execute if score {packId} {packId}_t matches ..1 run datapack disable {packId}', initFunction).implement()
    Statement(f'execute store success storage {packId} isCompatible int if score {packId} {packId}_t matches 2..', initFunction).implement()

  if defaultPackInfo:
    generateCode(mainCode[1:], None, "", "main.mcscript")
  else:
    generateCode(mainCode, None, "", "main.mcscript")

  print("looking for other files")
  for subdir, dirs, files in os.walk(os.getcwd()):
    dirs[:] = [d for d in dirs if not d[0] == "."]
    for file in files:
      if file.endswith(".mcscript") and not file == "main.mcscript":
        path = os.path.relpath(os.path.join(subdir, file))
        print(f"found file \"{path}\"")
        with open(path) as data:
          print("Converting to data pack form")
          generateCode(words(";", "".join(noComments(data)), [['"', '"', True], ["'", "'", True], ["{", "}"]], False, True), None, "/".join(path.split("/")[:-1]), file)

  print("Setting up listener calls")
  for key in listeners:
    if not key in internalListeners:
      scoresToReset = []
      listeners[key].sort(key=lambda x: x.priority)
      for function in listeners[key]:
        if not function.scoreId in variables:
          Comment(f"Used for listener {function.listenerId}", initFunction).implement()
          Statement(f'scoreboard objectives add {function.scoreId[:min([len(function.scoreId), 16])]} {function.listenerId}', initFunction).implement()
          #This line is only here so that the variable will register itself as visible to the rest of the program.
          #Initialization and manipulation are covered by other lines.
          Variable(packId, function.scoreId, "entity", "int", "0", f"Used for listener {function.listenerId}", False)

        Statement(f'execute as @e[scores={{{function.scoreId[:min([len(function.scoreId), 16])]}=1..}}] at @s run function {function.namespace}:{function.name}', tickFunction).implement()
        scoresToReset.append(function.scoreId[:min([len(function.scoreId), 16])])

      for score in scoresToReset:
        #Reset tje score
        Statement(f"scoreboard players set @e {score} 0", tickFunction).implement()
        #Remove the score on uninstall
        Statement(f"scoreboard objectives remove {score}", uninstallFunction).implement()

  if "tick" in listeners:
    listeners["tick"].sort(key=lambda x: x.priority)
    for function in listeners["tick"]:
      Statement(f"function {function.namespace}:{function.name}", tickFunction).implement()
  if "load" in listeners:
    listeners["load"].sort(key=lambda x: x.priority)
    for function in listeners["load"]:
      Statement(f"function {function.namespace}:{function.name}", initFunction).implement()
  if "uninstall" in listeners:
    listeners["uninstall"].sort(key=lambda x: x.priority)
    for function in listeners["uninstall"]:
      Statement(f"function {function.namespace}:{function.name}", uninstallFunction).implement()
  if "spawn" in listeners:
    listeners["spawn"].sort(key=lambda x: x.priority)
    for function in listeners["spawn"]:
      Statement(f"execute as @e[tag=!{packId}_spawned] at @s run function {function.namespace}:{function.name}", tickFunction).implement()
  
  #The "spawned" tag will be used by some other parts of the generator.
  Statement(f"tag @e[tag=!{packId}_spawned] add {packId}_spawned", tickFunction).implement()

  print('Adding "datapack loaded/unloaded" notification')
  Statement(f"execute store result score {packId} {packId}_t run data get storage {packId} isCompatible", initFunction).implement()
  initFunction.append(f'execute if score {packId} {packId}_t matches 1 run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully (re)loaded."}}]')
  Comment("Uninstall the pack if it is incompatible", initFunction).implement()
  Statement(f"execute if score {packId} {packId}_t matches 0 run function {uninstallFunction.name}", initFunction).implement()
  uninstallFunction.append(f'tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully unloaded."}}]')

  os.makedirs(f".saved/data", exist_ok = True)
  print("Saving functions for use in tags")
  with open(".saved/data/functions.csv", "w+") as file:
    data = ["namespace,name",f"{packId},internal/load", f"{packId},internal/tick", f"{packId},uninstall"]
    for i in customFunctions:
      print(f"Function {customFunctions[i].namespace}:{customFunctions[i].name} is defined. Adding it to the data.")
      data.append(f"{customFunctions[i].namespace},{customFunctions[i].name}")
    for i in externalFunctions:
      print(f'External function "{i.namespace}:{i.name}" is defined. Adding it to the data.')
      data.append(f"{i.namespace},{i.name}")
    file.write("\n".join(data))

  print("Generating tag files")
  tags.start(packName, packId, packDesc, useSnapshots)

  print("setting up data pack files")
  #Test
  os.makedirs(f".generated/packs/{packName}/data/minecraft/tags/functions", exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/functions/internal', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/blocks', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/entity_types', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/fluids', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/functions', exist_ok = True)
  os.makedirs(f'.generated/packs/{packName}/data/{packId}/tags/items', exist_ok = True)
  with open(f".generated/packs/{packName}/pack.mcmeta", "w+") as file:
    json.dump({"pack":{"pack_format":7 if useSnapshots else 6,"description": packDesc}}, file,indent=4)
  with open(f".generated/packs/{packName}/data/minecraft/tags/functions/load.json", "w+") as file:
    json.dump({"replace": False, "values":[f"{packId}:{initFunction.name}"]}, file,indent=4)
  with open(f".generated/packs/{packName}/data/minecraft/tags/functions/tick.json", "w+") as file:
    json.dump({"replace": False, "values":[f"{packId}:{tickFunction.name}"]}, file,indent=4)

  print("Writing init function to data pack")
  initFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/{initFunction.name}.mcfunction")
  print("Writing uninstall function to data pack")
  uninstallFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/{uninstallFunction.name}.mcfunction")
  print("Writing tick function to data pack")
  tickFunction.implement(f".generated/packs/{packName}/data/{packId}/functions/{tickFunction.name}.mcfunction")
  for name in customFunctions:
    print(f'Writing "{name}" function to data pack')
    os.makedirs(f".generated/packs/{packName}/data/{packId}/functions/{customFunctions[name].path}", exist_ok=True)
    customFunctions[name].implement(f".generated/packs/{packName}/data/{packId}/functions/{name}.mcfunction")
  
  print("Done")

if __name__ == "__main__":
  main()
  #tags.start()
  #convert.start()
  #regex_test.start()
