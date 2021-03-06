import os
import json
import tags
import shutil
import re
import sys

#import convert


def isUnescaped(string, index, escapeChar):
    if index < 0:
        index = len(string) + index
    ind = re.escape(string[index])
    regex = f"(?:(?<!{escapeChar})(?:{escapeChar}(?:{escapeChar}(?:{escapeChar}{{2}})*))?)({ind})"
    for match in re.finditer(regex, string[:index + 1]):
        if match.start(1) == index:
            return True
    return False


def isEscaped(string, index, escapeChar):
    if index < 0:
        index = len(string) + index
    ind = re.escape(string[index])
    regex = f"(?:(?<!{escapeChar})(?:{escapeChar}(?:{escapeChar}{{2}})*))({ind})"
    for match in re.finditer(regex, string[:index + 1]):
        if match.start(1) == index:
            return True
    return False


def update_namespace(file_path, namespace, name):
    from tempfile import mkstemp
    from shutil import move, copymode
    from os import fdopen, remove
    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                if not line.strip()[0] == "#":
                    new_file.write(
                        line.replace(
                            f"{name}:", f"{namespace}:{name}/").replace(
                                f"storage {name}",
                                f"storage {namespace}:{name}").replace(
                                    f'"storage":"{name}"',
                                    f'"storage":"{namespace}:{name}"').replace(
                                        f"tag={name}_",
                                        f"tag={namespace}_{name}_").replace(
                                            "${namespace}", namespace))
                else:
                    new_file.write(line)
    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)


"""
Given a list of lists (or ranges) [li], return if [x] is included in any of them
"""


def inAny(x, li):
    for i in li:
        if x in i:
            return True

    return False


def segment(s, i, string):
    for ind in range(0, len(s)):
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


def ignoreIndexes(string, ignoreChars, inclusive, escapeChar=r"\\"):
    altInds = []
    if (len(ignoreChars) > 1):
        for i in ignoreChars:
            altInds.extend(
                ignoreIndexes(string, [i], False, escapeChar=escapeChar))

    result = []
    ignore = False
    ignoreCount = 0
    ignoreList = None
    startIndex = -1

    for i in range(0, len(string)):
        if (not ignoreList == None
            ) and len(ignoreList) > 2 and ignoreList[2] == True and isEscaped(
                string, i, escapeChar):
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
                    result.append(
                        range(startIndex + int(not inclusive),
                              i + int(inclusive)))
                    startIndex = -1
        elif ignoreList[1] == c and not inAny(i, altInds):
            ignoreCount = 0
            ignoreList = None
            ignore = False
            result.append(
                range(startIndex + int(not inclusive), i + int(inclusive)))
            startIndex = -1

    return result


"""
Get the strings associated with a specific call of ignoreIndexes
"""


def groups(string, ignoreChars, inclusive, requiredPair=None, escapeChar="\\"):
    result = []
    indexes = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))
    for r in indexes:
        result.append(string[r[0]:r[-1] + 1])

    if requiredPair != None:
        for s in result:
            if not (s[0] == requiredPair[0] and s[-1] == requiredPair[1]):
                result.remove(s)

    if not inclusive:
        for i in range(0, len(result)):
            result[i] = result[i][1:-1]

    for i in range(0, len(result)):
        for ignoreChar in ignoreChars:
            if len(ignoreChar) > 2 and ignoreChar[2]:
                result[i] = result[i].replace(
                    f"{escapeChar}{ignoreChar[0]}",
                    f"{ignoreChar[0]}").replace(f"{escapeChar}{ignoreChar[1]}",
                                                f"{ignoreChar[1]}")
        result[i] = result[i].replace(escapeChar * 2, escapeChar)

    return result


"""
Return the first appearance of {character} in {string} that is not part of a group defined by {ignoreChars}
(see ignoreIndexes)
"""


def indexOf(character, string, ignoreChars, escapeChar="\\"):
    ignoreInds = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))

    for i in range(0, len(string)):
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
        hashtagIndex = indexOf(
            "#", line, [["\"", "\""], ["[", "]"], ["/", ";"], ["(", ")"]])
        if hashtagIndex > 0:
            result.append(line[:hashtagIndex].strip())
        elif hashtagIndex != 0 and len(line) > 0:
            result.append(line)

    return result


"""
Return a list of elements separated by {separator} in {string}, grouping using the {ignoreChars}
(see ignoreIndexes)
"""


def words(separator,
          string,
          ignoreChars,
          separatorInclusive,
          ignoreCharInclusive,
          escapeChar="\\"):
    result = [""]
    ignoreInds = ignoreIndexes(
        string, ignoreChars, True, escapeChar=re.escape(escapeChar))
    skip = 0

    for i in range(0, len(string)):
        if skip > 0:
            skip -= 1
        else:
            if (not inAny(i, ignoreInds)) and segment(separator, i, string):
                if separatorInclusive:
                    result[-1] += separator
                result.append("")
                skip = len(separator) - 1
            elif ignoreCharInclusive or not (
                    i >= 2 and inAny(string[i], ignoreChars)
                    and isUnescaped(string, i, re.escape(escapeChar))):
                result[-1] += string[i]

    if result[-1] == "":
        result = result[:len(result) - 1]

    for i in range(0, len(result)):
        for ignoreChar in ignoreChars:
            if len(ignoreChar) > 2 and ignoreChar[2]:
                result[i] = result[i].replace(
                    f"{escapeChar}{ignoreChar[0]}",
                    f"{ignoreChar[0]}").replace(f"{escapeChar}{ignoreChar[1]}",
                                                f"{ignoreChar[1]}")
        result[i] = result[i].replace(escapeChar * 2, escapeChar)

    return result


class Statement:
    def __init__(self, text, parentFunction):
        self.text = text
        self.parentFunction = parentFunction

    def implement(self):
        self.parentFunction.append(self.text)


class Comment(Statement):
    def implement(self):
        if self.text[0] == "#":
            self.parentFunction.append(
                re.sub(r"(?:(?<!\\)(?:\\(?:\\(?:\\{2})*))?)(\\n)", r"\n#",
                       self.text.replace("\\\\", "\\")))
        else:
            self.parentFunction.append(
                "#" + re.sub(r"(?:(?<!\\)(?:\\(?:\\(?:\\{2})*))?)(\\n)",
                             r"\n#", self.text.replace("\\\\", "\\")))


class LiteralCommand(Statement):
    def implement(self):
        global constantVariables
        global packId

        offset = 0
        for match in re.finditer(r'<\s*(?P<variable>[a-z0-9_]+)(\.json)?\s*>',
                                 self.text):
            if isUnescaped(self.text, match.start() - offset, r"<"):
                name = match.group("variable")
                print(
                    f'Found variable "{name}" called in command "{self.text}"')
                if name in constantVariables:
                    print("filling in the value")
                    if not "entity" in constantVariables[name].type:
                        value = str(constantVariables[name].value)
                        if constantVariables[name].type == "float":
                            value += "f"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"text": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                    elif constantVariables[name].type == "entity[]":
                        value = f"@e[tag=in_{packId}_{name}]"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"selector": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                    elif constantVariables[name].type == "entity":
                        value = f"@e[tag={packId}_{name},limit=1]"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"selector": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                elif name in variables:
                    if variables[name].modifier == "entity":
                        pass
                    else:
                        print("filling in the value")
                        if not "entity" in variables[name].type:
                            obj = {"nbt": f"vars.{name}", "storage": packId}
                            value = json.dumps(obj)
                            self.text = self.text[:match.start(
                            ) - offset] + value + self.text[match.end() -
                                                            offset:]
                            offset += len(match.group()) - len(value)
                else:
                    print(
                        "variable does not exist, so value will be left as-is."
                    )
        self.text = self.text.replace("<<", "<").replace(">>", ">")

        if self.text[0] == "/":
            self.parentFunction.append(self.text[1:])
        else:
            self.parentFunction.append(self.text)


class CallFunction(LiteralCommand):
    def __init__(self, functionName, parentFunction):
        super().__init__("/function " + functionName, parentFunction)


class Variable:
    def __init__(self, namespace, name, modifier, t, value, desc, define):
        global constantVariables
        if value != None:
            value = value.strip()

        self.namespace = namespace
        self.modifier = modifier
        self.type = t
        self.name = name

        if modifier == "constant":
            constantVariables[self.name] = self

        if segment("float", 0, self.type):
            if "[]" in self.type:
                self.type = "float[]"
            else:
                self.type = "float"

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
                self.value = groups(self.value,
                                    [['"', '"', True], ["'", "'", True]],
                                    False)[0].replace("\\\\", "\\").replace(
                                        '\\"', '"').replace("\\'", "'")
            elif "[]" in self.type:
                self.value = []
                for item in words(",", value[1:-1],
                                  [['"', '"', True], ["'", "'", True],
                                   ["{", "}"], ["[", "]"], ["(", ")"]], False,
                                  True):
                    item = item.strip()
                    if "int" in self.type:
                        self.value.append(int(item))
                    elif "float" in self.type:
                        self.value.append(float(item[:-1]))
                    elif "string" in self.type:
                        self.value.append(
                            groups(item, [['"', '"', True], ["'", "'", True]],
                                   False)[0].replace("\\\\", "\\").replace(
                                       '\\"', '"').replace("\\'", "'"))
                    else:
                        self.value.append(item)

        variables[self.name] = self
        if define:
            DefineVariable(self, initFunction).implement()


class DefineVariable(Statement):
    def __init__(self, variable, parentFunction):
        text = ""
        if variable.desc != None:
            newDesc = re.sub(r"(?:(?<!\\)(?:\\(?:\\(?:\\{2})*))?)(\\n)",
                             r"\n#" + (" " * (len(variable.name) + 13)),
                             variable.desc.replace("\\\\", "\\"))
            Comment(f'variable "{variable.name}": {newDesc}',
                    parentFunction).implement()
        else:
            Comment(f'variable "{variable.name}"', parentFunction).implement()

        if variable.value != None:
            if variable.modifier == "constant":
                if not "entity" in variable.type:
                    stringForm = f'"{variable.value}"'
                    text = f'data modify storage {packId} constants.{variable.name} set value {variable.value if variable.type != "string" else stringForm}'
                    if variable.type == "float":
                        text += "f"
                elif variable.type == "entity[]":
                    if len(variable.value) > 0:
                        text = f'#variable "{variable.name}" Initialization index 0'
                        text += f"\ntag {variable.value[0]} add in_{packId}_{variable.name}"
                        if len(variable.value) > 1:
                            index = 1
                            for i in variable.value[1:]:
                                text += f"\n#variable \"{variable.name}\" Initialization index {index}\ntag {i} add in_{packId}_{variable.name}"
                                index += 1
                elif variable.type == "entity":
                    #Ensure the limit is 1
                    args = groups(variable.value, [["[", "]"]], False)
                    if len(args) > 0:
                        args = args[0]
                        argList = words(",", args,
                                        [['"', '"', True], ["'", "'", True],
                                         ["(", ")"], ["{", "}"], ["[", "]"]],
                                        False, True)
                        if not "limit=1" in argList:
                            variable.value = variable.value.replace(
                                args, args + ",limit=1")
                    elif variable.value[0] == "@":
                        variable.value += "[limit=1]"

                    text = f"tag {variable.value} add {packId}_{variable.name}"
            elif variable.modifier == "global":
                if not "entity" in variable.type:
                    stringForm = f'"{variable.value}"'
                    text = f'data modify storage {packId} vars.{variable.name} set value {variable.value if variable.type != "string" else stringForm}'
                    if variable.type == "float":
                        text += "f"
                elif variable.type == "entity[]":
                    if len(variable.value) > 0:
                        text = f'#variable "{variable.name}" Initialization index 0'
                        text += f"\ntag {variable.value[0]} add in_{packId}_{variable.name}"
                        if len(variable.value) > 1:
                            index = 1
                            for i in variable.value[1:]:
                                text += f"\n#variable \"{variable.name}\" Initialization index {index}\ntag {i} add in_{packId}_{variable.name}"
                                index += 1
                elif variable.type == "entity":
                    #Ensure the limit is 1
                    args = groups(variable.value, [["[", "]"]], False)
                    if len(args) > 0:
                        args = args[0]
                        argList = words(",", args,
                                        [['"', '"', True], ["'", "'", True],
                                         ["(", ")"], ["{", "}"], ["[", "]"]],
                                        False, True)
                        if not "limit=1" in argList:
                            variable.value = variable.value.replace(
                                args, args + ",limit=1")
                    elif variable.value[0] == "@":
                        variable.value += "[limit=1]"

                    text = f"tag {variable.value} add {packId}_{variable.name}"
        else:
            text = f"#The {variable.modifier} variable \"{variable.name}\" is defined, but has no initializing value."

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

        if desc != None:
            Comment(desc, self).implement()

    def append(self, value):
        self.code.append(value)

    def implement(self, filePath):
        if len(self.code) > 0:
            with open(filePath, "w+") as file:
                file.write("\n".join(self.code))


class ExecuteWrapper(Function):
    def __init__(self, conditions, code, parentFunction):
        self.conditions = conditions
        self.parentFunction = parentFunction
        super().__init__(parentFunction.namespace, parentFunction.name, None,
                         None)

    def implement(self):
        for i in range(0, len(self.code)):
            self.code[i] = "execute " + " ".join(
                self.conditions) + " run " + self.code[i]
            self.parentFunction.append(self.code[i])


packName = "Generated Data Pack"
packId = "generated_data_pack"
packDesc = "Data pack generated from a Minecraft Programming Language compiler"
packShort = "gdp"
defaultPackInfo = False
useSnapshots = False

preinitFunction = Function(
    packId, "internal/preload",
    "It is necessary to delay the load function by 1 second so that it may be run on world load correctly.",
    0)
initFunction = Function(packId, "internal/load",
                        "This function is run when the datapack is loaded.", 0)
uninstallFunction = Function(
    packId, "uninstall",
    "Can be called to remove the pack and any trace it was ever installed", 0)
tickFunction = Function(
    packId, "internal/tick",
    "This function is run every tick after this datapack is loaded.", 0)
customFunctions = {
    "exists":
    Function(packId, "exists",
             "If you can successfully run this function, the pack exists.", 0)
}
listeners = {}
externalFunctions = []
requiredPacks = []
internalListeners = ["load", "tick", "uninstall", "spawn"]
variables = {}
constantVariables = {}
playerPreference = "both"
libraries = []


def generateCode(code, function, path, file, parentScript):
    global listeners
    global externalFunctions
    global customFunctions
    global requiredPacks
    global packId
    global libraries

    if function == None:
        #Top-level statements: Variables and function declarations
        for line in code:
            #Listener definition
            match = re.match(
                r'(priority\=(?P<priority>[+-]?\d+)\s+)?(id="(?P<id>[^\"]+)"\s+)?on\s+(?P<name>[a-z_0-9\.\:]+)',
                line)
            if match != None:
                name = match.group("name").replace(":", "_")
                id = match.group("id")
                priority = match.group("priority")
                if not name in listeners:
                    listeners[name] = []
                version = len(listeners[name]) + 1
                function = None
                if priority == None:
                    function = Function(
                        packId,
                        f"listeners/{name}/{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}{version}",
                        f"This function is called for every {name} event with 0 priority",
                        0)
                else:
                    priority = int(priority)
                    function = Function(
                        packId,
                        f"listeners/{name}/{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}{version}",
                        f"This function is called for every {name} event with {priority} priority",
                        priority)

                function.listenerId = match.group("name")
                function.scoreId = name
                if id != None:
                    function.scoreId = id

                statements = words(
                    ";",
                    groups(
                        line, [["{", "}"], ['"', '"', True]],
                        False,
                        requiredPair=["{", "}"])[0],
                    [['"', '"', True], ["'", "'", True], ["{", "}"],
                     ["[", "]"]], False, True)
                customFunctions[function.name] = function
                listeners[name].append(function)
                generateCode(statements, function, function.path,
                             f"{name.replace('.', '_')}-{version}.mcscript",
                             parentScript)
            else:
                #Function definition
                match = re.match(
                    r'function\s+(desc="(?P<desc>[^\"]+)"\s+)?(?P<name>[a-z_]+)\(\)',
                    line)
                if match != None:
                    name = match.group("name")
                    desc = match.group("desc")
                    function = None
                    if desc == None:
                        function = Function(
                            packId,
                            f"{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}",
                            f"The function defined with the name '{name}' in the file '{path}/{file}'",
                            0)
                    else:
                        function = Function(
                            packId,
                            f"{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}",
                            desc, 0)
                    statements = words(";",
                                       groups(line, [["{", "}"]], False)[0],
                                       [['"', '"', True], ["'", "'", True],
                                        ["{", "}"], ["[", "]"]], False, True)
                    customFunctions[function.name] = function
                    generateCode(statements, function, function.path,
                                 function.name, parentScript)
                else:
                    #External function definition
                    match = re.match(
                        r'def (?P<namespace>[a-z_]+):(?P<name>[a-z_\/]+)',
                        line)
                    if match != None:
                        externalFunctions.append(
                            Function(
                                match.group("namespace"), match.group("name"),
                                "", 0))
                    else:
                        #Variable definition
                        match = re.match(
                            r'(?P<modifier>global|entity|constant)\s+(desc="(?P<desc>[^\"]+)"\s+)?(?P<type>(?:entity|int|float|string|bool)(?:\<\d+\>)?(?:\[\])?)\s+(?P<name>[a-zA-Z_]+)(\s*\=\s*(?P<value>.+))?',
                            line)
                        if match != None:
                            modifier = match.group("modifier")
                            t = match.group("type")
                            name = match.group("name")
                            value = match.group("value")
                            desc = match.group("desc")
                            print(f'Defining variable "{name}"')
                            Variable(packId, name, modifier, t, value, desc,
                                     True)
                        else:
                            #Required pack definition
                            match = re.match(
                                r'require\s+(?P<namespace>[a-z_]+)', line)
                            if match != None:
                                requiredPacks.append(match.group("namespace"))
                            else:
                                pass
    else:
        #Lower level satements - Instructions
        for line in code:
            #Literal command
            if line[0] == "/":
                LiteralCommand(line, function).implement()
            else:
                match = re.match(r'comment((?P<message>.+))(\)$)', line)
                if match != None:
                    message = groups(
                        match.group("message"), [['"', '"', True]], False)[0]
                    Comment(message, function).implement()
                else:
                    match = re.match(
                        r'(?P<function>[a-z_0-9\.]+(:)?[a-z_0-9\.]+)(?<!\.)\(\)',
                        line)
                    if match != None:
                        f = match.group("function")
                        functionList = f.split(":")
                        if len(functionList) < 2:
                            functionList = f.split(".")
                            if len(functionList) == 1:
                                CallFunction(
                                    f"{packId}:{parentScript}/{functionList[0]}",
                                    function).implement()
                            else:
                                CallFunction(
                                    f"{packId}:{'/'.join(functionList)}",
                                    function).implement()
                        else:
                            namespace = functionList[0]
                            functionList = functionList[1].split(".")
                            CallFunction(
                                f"{namespace}:{'/'.join(functionList)}",
                                function).implement()
                    else:
                        match = re.match(
                            r'(?P<conditions>((if|unless|store|align|anchored|as|at|facing|positioned|rotated)(.)+?\s*)+?)\s*{(?P<code>(.|\s)*)}',
                            line)
                        if match != None:
                            conditions = []
                            conditionsWords = words(
                                " ", match.group("conditions"),
                                [['"', '"', True], ["'", "'", True],
                                 ["(", ")"]], False, True)
                            for condition in conditionsWords:
                                if condition == "":
                                    continue
                                elif condition in [
                                        "if", "unless", "store", "align",
                                        "anchored", "as", "at", "facing",
                                        "positioned", "rotated"
                                ]:
                                    conditions.append(condition)
                                elif condition[0] == "(" and condition[
                                        -1] == ")":
                                    conditions[-1] += " " + condition[1:-1]
                                else:
                                    conditions[-1] += " " + condition

                            statements = words(
                                ";", match.group("code"),
                                [['"', '"', True], ["'", "'", True],
                                 ["(", ")"], ["[", "]"], ["{", "}"]], False,
                                True)

                            if len(statements) == 1:
                                wrapper = ExecuteWrapper(
                                    conditions, [], function)
                                generateCode(statements, wrapper, path, file,
                                             parentScript)
                                wrapper.implement()
                        else:
                            pass


def main():
    global packId
    global packDesc
    global packName
    global useSnapshots
    global packDesc
    global variables
    global playerPreference
    global packShort
    global requiredPacks

    print("Start")

    mainCode = []
    with open("main.mcscript", "r") as data:
        print("found main file")
        codeList = noComments(data)
        #A list of each separate statement or definition without any new lines or tabs
        mainCode = words(";", "".join(codeList),
                         [['"', '"', True], ["'", "'", True], ["(", ")"],
                          ["[", "]"], ["{", "}"]], False, True)
    """print("main file contents:")
    for i in range(0,len(mainCode)):
      print(f"\t{i}: {mainCode[i]}")"""

    if segment("pack-info: ", 0, mainCode[0]):
        info = packId = words(" ", mainCode[0],
                              [['"', '"', True], ["'", "'", True]], False,
                              False)[1:]
        packName = info[0]
        packId = info[1]
        packShort = info[2]
        packDesc = info[3]
        print(f'got pack name "{packName}" with id "{packId}"')
        useSnapshots = info[4].lower().capitalize()
        if useSnapshots == "True":
            print("Snapshots have been enabled. Pack format changed to 7.")
        else:
            print("No snapshots are in use. Pack format is 6.")
        playerPreference = info[5].lower()
        defaultPackInfo = False
        print("Converting to data pack form")
    else:
        print(
            f'no pack info specified. Default values will be used (name "{packName}" id {packId})'
        )
        defaultPackInfo = True

    if os.path.isdir(f".generated/packs/{packName}"):
        print("Cleaning up previous generation files")
        while os.path.isdir(f".generated/packs/{packName}"):
            shutil.rmtree(f".generated/packs/{packName}")

    print("Populating default function statements")
    Statement(f"schedule function {packId}:{initFunction.name} 1s replace",
              preinitFunction).implement()

    Statement(f"scoreboard objectives add {packShort}_temp dummy",
              initFunction).implement()
    Statement(f"scoreboard objectives remove {packShort}_temp",
              uninstallFunction).implement()
    Statement(f"scoreboard players set {packId} {packShort}_temp 0",
              initFunction).implement()
    #This line is only here so that the variable will register itself as visible to the rest of the program.
    #Initialization and manipulation are covered by other lines.
    Variable(packId, f"{packShort}_temp", "entity", "int", "0",
             f"Temporary score for this pack.", False)
    if playerPreference == "single":
        Statement("", initFunction).implement()
        Comment("Ensure the game is run in singleplayer",
                initFunction).implement()
        Statement(
            f"execute as @a run scoreboard players add {packId} {packShort}_temp 1",
            initFunction).implement()
        Statement(
            f'execute if score {packId} {packShort}_temp matches 2.. run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with singleplayer.\\nDisabling the pack to avoid unexpected behavior.\\nUse "}},{{"text":"/datapack enable \\"file/{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"Click to copy this command to the chat bar."}}]}},"clickEvent":{{"action":"suggest_command","value":"/datapack enable \\"file/{packName}\\""}}}},{{"text":" To reenable."}}]',
            initFunction).implement()
        Statement(
            f'execute if score {packId} {packShort}_temp matches 2.. run datapack disable "file/{packName}"',
            initFunction).implement()
        Statement(
            f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches ..1',
            initFunction).implement()
    elif playerPreference == "multi":
        Statement("", initFunction).implement()
        Comment("Ensure the game is run in multiplayer",
                initFunction).implement()
        Statement(
            f"execute as @a run scoreboard players add {packId} {packShort}_temp 1",
            initFunction).implement()
        Statement(
            f'execute if score {packId} {packShort}_temp matches ..1 run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with multiplayer.\\nDisabling the pack to avoid unexpected behavior.\\nUse "}},{{"text":"/datapack enable \\"file/{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"Click to copy this command to the chat bar."}}]}},"clickEvent":{{"action":"suggest_command","value":"/datapack enable \\"file/{packName}\\""}}}},{{"text":" To reenable."}}]',
            initFunction).implement()
        Statement(
            f'execute if score {packId} {packShort}_temp matches ..1 run datapack disable "file/{packName}"',
            initFunction).implement()
        Statement(
            f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches 2..',
            initFunction).implement()

    #Add a new line to the function
    Statement("", initFunction).implement()

    if defaultPackInfo:
        generateCode(mainCode[1:], None, "", "main.mcscript", "main")
    else:
        generateCode(mainCode, None, "", "main.mcscript", "main")

    libraryFiles = []
    libraryNamespaces = []
    print("looking for other files")
    for subdir, dirs, files in os.walk(os.getcwd()):
        dirs[:] = [
            d for d in dirs if not d[0] == "." and not d == "__pycache__"
        ]
        for file in files:
            if not file == "main.mcscript":
                path = os.path.relpath(os.path.join(subdir, file))
                if file.endswith(".mcscript"):
                    print(f"found file \"{path}\"")
                    with open(path) as data:
                        print("Converting to data pack form")
                        generateCode(
                            words(";", "".join(noComments(data)),
                                  [['"', '"', True], ["'", "'", True],
                                   ["{", "}"]], False, True), None, "/".join(
                                       path.split("/")[:-1]), file,
                            file.split(".")[:-1])
                elif not file.endswith(".mctag") and not file.endswith(
                        ".py") and not path == "README.md":
                    print(f"found file \"{path}\"")
                    print("copying it to the datapack")

                    if path[0] == "#":
                        print("copying as library file")
                        pathList = []
                        if sys.platform == "win32":
                            pathList = path.split("\\")
                        else:
                            pathList = path.split("/")

                        pathList[0] = pathList[0][1:]
                        name = pathList[0]
                        if not name in libraryNamespaces:
                            libraryNamespaces.append(name)
                        if len(pathList) > 2:
                            pathList[0], pathList[1] = pathList[1], pathList[0]
                            p = "/".join(pathList[1:-1]
                                         ) + "/" + pathList[-1].split(".")[0]
                            if pathList[0] == "functions" and pathList[
                                    -1].endswith(".mcfunction"):
                                customFunctions[p] = Function(
                                    packId, p, "Imported from a library", 0)

                        pathList = pathList[:-1]
                        os.makedirs(
                            f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}",
                            exist_ok=True)
                        shutil.copyfile(
                            path,
                            f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}/{file}"
                        )
                        if not f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}/{file}" in libraryFiles:
                            libraryFiles.append(
                                f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}/{file}"
                            )
                    else:
                        os.makedirs(
                            f".generated/packs/{packName}/data/{packId}/{os.path.relpath(subdir)}",
                            exist_ok=True)
                        shutil.copyfile(
                            path,
                            f".generated/packs/{packName}/data/{packId}/{path}"
                        )

    for name in libraryNamespaces:
        libraries.append(name)
        print(f'updating namespace calls from "{name}" to "{packId}:{name}/"')
        for path in libraryFiles:
            update_namespace(path, packId, name)

    print("Requiring packs")
    if len(requiredPacks) > 0:
        Comment("Ensure all required packs are installed.",
                initFunction).implement()
        for pack in requiredPacks:
            Statement(
                f"execute if data storage {packId} {{isCompatible:1}} store success score {packId} {packShort}_temp run function {pack}:exists",
                initFunction).implement()
            Statement(
                f'execute if score {packId} {packShort}_temp matches 0 run tellraw @a {{"text":"The required pack \"{pack}\" was not detected to exist.\\n Disabling to avoid unexpected behavior.","color":"red"}}',
                initFunction).implement()
            Statement(
                f'execute if score {packId} {packShort}_temp matches 0 run datapack disable "file/{packName}"',
                initFunction).implement()
            Statement(
                f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches 1',
                initFunction).implement()
            Statement("", initFunction).implement()

    print("Setting up listener calls")
    for key in listeners:
        if not key in internalListeners:
            scoresToReset = []
            listeners[key].sort(key=lambda x: x.priority)
            for function in listeners[key]:
                if not function.scoreId in variables:
                    Comment(f"Used for listener {function.listenerId}",
                            initFunction).implement()
                    Statement(
                        f'scoreboard objectives add {function.scoreId[:min([len(function.scoreId), 16])]} {function.listenerId}',
                        initFunction).implement()
                    #This line is only here so that the variable will register itself as visible to the rest of the program.
                    #Initialization and manipulation are covered by other lines.
                    Variable(packId, function.scoreId, "entity", "int", "0",
                             f"Used for listener {function.listenerId}", False)

                Statement("", tickFunction).implement()
                Comment("Run listeners", tickFunction).implement()
                Statement(
                    f'execute as @e[scores={{{function.scoreId[:min([len(function.scoreId), 16])]}=1..}}] at @s run function {function.namespace}:{function.name}',
                    tickFunction).implement()
                scoresToReset.append(
                    function.scoreId[:min([len(function.scoreId), 16])])

            if len(scoresToReset) > 0:
                Statement("", tickFunction).implement()
                Comment("Reset listener scores", tickFunction).implement()
            for score in scoresToReset:
                #Reset the score
                Statement(f"scoreboard players set @e {score} 0",
                          tickFunction).implement()
                #Remove the score on uninstall
                Statement(f"scoreboard objectives remove {score}",
                          uninstallFunction).implement()

    if "tick" in listeners:
        #Add a new line to the function
        Statement("", tickFunction).implement()
        Comment("Run tick listeners", tickFunction).implement()
        listeners["tick"].sort(key=lambda x: x.priority)
        for function in listeners["tick"]:
            Statement(f"function {function.namespace}:{function.name}",
                      tickFunction).implement()
    if "load" in listeners:
        #Add a new line to the function
        Statement("", initFunction).implement()
        Comment("Run listeners", initFunction).implement()
        listeners["load"].sort(key=lambda x: x.priority)
        for function in listeners["load"]:
            Statement(f"function {function.namespace}:{function.name}",
                      initFunction).implement()
    if "uninstall" in listeners:
        #Add a new line to the function
        Statement("", uninstallFunction).implement()
        Comment("Run listeners", uninstallFunction).implement()
        listeners["uninstall"].sort(key=lambda x: x.priority)
        for function in listeners["uninstall"]:
            Statement(f"function {function.namespace}:{function.name}",
                      uninstallFunction).implement()
    if "spawn" in listeners:
        #Add a new line to the function
        Statement("", tickFunction).implement()
        Comment("Run spawn listeners", tickFunction).implement()
        listeners["spawn"].sort(key=lambda x: x.priority)
        for function in listeners["spawn"]:
            Statement(
                f"execute as @e[tag=!{packId}_spawned] at @s run function {function.namespace}:{function.name}",
                tickFunction).implement()

    #The "spawned" tag will be used by some other parts of the generator.
    Statement(f"tag @e[tag=!{packId}_spawned] add {packId}_spawned",
              tickFunction).implement()

    print('Adding "datapack loaded/unloaded" notification')
    #Add a new line to the function
    Statement("", initFunction).implement()
    Comment("Uninstall if incompatible", initFunction).implement()
    initFunction.append(
        f'execute if data storage {packId} {{isCompatible:1}} run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully (re)loaded."}}]'
    )
    Comment("Uninstall the pack if it is incompatible",
            initFunction).implement()
    Statement(
        f"execute if data storage {packId} {{isCompatible:0}} run function {packId}:{uninstallFunction.name}",
        initFunction).implement()

    for lib in libraries:
        uninstallFunction.append(f'function {packId}:{lib}/uninstall')
    #Add a new line to the function
    Statement("", uninstallFunction).implement()
    uninstallFunction.append(
        f'tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully unloaded."}}]'
    )
    Statement(f'datapack disable "file/{packName}"',
              uninstallFunction).implement()
    Statement("", initFunction).implement()
    Comment("Start the tick function", initFunction).implement()
    Statement(
        f"execute if score {packId} {packShort}_temp matches 1 run function {packId}:{tickFunction.name}",
        initFunction).implement()
    Statement("", tickFunction).implement()
    Comment("Start the tick function again next tick",
            tickFunction).implement()
    Statement(f"schedule function {packId}:{tickFunction.name} 1t replace",
              tickFunction).implement()

    os.makedirs(f".saved/data", exist_ok=True)
    print("Saving functions for use in tags")
    with open(".saved/data/functions.csv", "w+") as file:
        data = [
            "namespace,name", f"{packId},internal/load",
            f"{packId},internal/preload", f"{packId},internal/tick",
            f"{packId},uninstall"
        ]
        for i in customFunctions:
            customFunctions[i].namespace = packId
            print(
                f"Function \"{customFunctions[i].namespace}:{customFunctions[i].name}\" is defined. Adding it to the data."
            )
            data.append(
                f"{customFunctions[i].namespace},{customFunctions[i].name}")

        for i in externalFunctions:
            print(
                f'External function "{i.namespace}:{i.name}" is defined. Adding it to the data.'
            )
            data.append(f"{i.namespace},{i.name}")
        file.write("\n".join(data))

    print("Generating tag files")
    tags.start(packName, packId, packDesc, useSnapshots)

    print("setting up data pack files")

    os.makedirs(
        f".generated/packs/{packName}/data/minecraft/tags/functions",
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/functions/internal',
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/tags/blocks',
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/tags/entity_types',
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/tags/fluids',
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/tags/functions',
        exist_ok=True)
    os.makedirs(
        f'.generated/packs/{packName}/data/{packId}/tags/items', exist_ok=True)
    with open(f".generated/packs/{packName}/pack.mcmeta", "w+") as file:
        json.dump({
            "pack": {
                "pack_format": 7 if useSnapshots else 6,
                "description": packDesc
            }
        },
                  file,
                  indent=4)
    with open(
            f".generated/packs/{packName}/data/minecraft/tags/functions/load.json",
            "w+") as file:
        json.dump({
            "replace": False,
            "values": [f"{packId}:{preinitFunction.name}"]
        },
                  file,
                  indent=4)

    print("Writing preinit function to data pack")
    preinitFunction.implement(
        f".generated/packs/{packName}/data/{packId}/functions/{preinitFunction.name}.mcfunction"
    )
    print("Writing init function to data pack")
    initFunction.implement(
        f".generated/packs/{packName}/data/{packId}/functions/{initFunction.name}.mcfunction"
    )
    print("Writing uninstall function to data pack")
    uninstallFunction.implement(
        f".generated/packs/{packName}/data/{packId}/functions/{uninstallFunction.name}.mcfunction"
    )
    print("Writing tick function to data pack")
    tickFunction.implement(
        f".generated/packs/{packName}/data/{packId}/functions/{tickFunction.name}.mcfunction"
    )
    for name in customFunctions:
        print(f'Writing "{name}" function to data pack')
        os.makedirs(
            f".generated/packs/{packName}/data/{packId}/functions/{customFunctions[name].path}",
            exist_ok=True)
        customFunctions[name].implement(
            f".generated/packs/{packName}/data/{packId}/functions/{name}.mcfunction"
        )

    print("Done")


if __name__ == "__main__":
    main()
    #tags.start()
    #convert.start()
    #regex_test.start()
