import json
import re
from tools import *
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

import main

class LiteralCommand(Statement):
    def implement(self):
        offset = 0
        for match in re.finditer(r'<\s*(?P<variable>[a-z0-9_]+)(\.json)?\s*>',
                                 self.text):
            if isUnescaped(self.text, match.start() - offset, r"<"):
                name = match.group("variable")
                print(
                    f'Found variable "{name}" called in command "{self.text}"')
                if name in main.constantVariables:
                    print("filling in the value")
                    if not "entity" in main.constantVariables[name].type:
                        value = str(main.constantVariables[name].value)
                        if main.constantVariables[name].type == "float":
                            value += "f"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"text": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                    elif main.constantVariables[name].type == "entity[]":
                        value = f"@e[tag=in_{main.packId}_{name}]"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"selector": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                    elif main.constantVariables[name].type == "entity":
                        value = f"@e[tag={main.packId}_{name},limit=1]"
                        if ".json" in match.group():
                            print(
                                "Requested JSON value. Wrapping around JSON object"
                            )
                            value = json.dumps({"selector": value})
                        self.text = self.text[:match.start(
                        ) - offset] + value + self.text[match.end() - offset:]
                        offset += len(match.group()) - len(value)
                elif name in main.variables:
                    if main.variables[name].modifier == "entity":
                        pass
                    else:
                        print("filling in the value")
                        if not "entity" in main.variables[name].type:
                            obj = {"nbt": f"vars.{name}", "storage": main.packId}
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
        if value != None:
            value = value.strip()

        self.namespace = namespace
        self.modifier = modifier
        self.type = t
        self.name = name

        if modifier == "constant":
            main.constantVariables[self.name] = self

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

        main.variables[self.name] = self
        if define:
            DefineVariable(self, main.initFunction).implement()


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
                    text = f'data modify storage {main.packId} constants.{variable.name} set value {variable.value if variable.type != "string" else stringForm}'
                    if variable.type == "float":
                        text += "f"
                elif variable.type == "entity[]":
                    if len(variable.value) > 0:
                        text = f'#variable "{variable.name}" Initialization index 0'
                        text += f"\ntag {variable.value[0]} add in_{main.packId}_{variable.name}"
                        if len(variable.value) > 1:
                            index = 1
                            for i in variable.value[1:]:
                                text += f"\n#variable \"{variable.name}\" Initialization index {index}\ntag {i} add in_{main.packId}_{variable.name}"
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

                    text = f"tag {variable.value} add {main.packId}_{variable.name}"
            elif variable.modifier == "global":
                if not "entity" in variable.type:
                    stringForm = f'"{variable.value}"'
                    text = f'data modify storage {main.packId} vars.{variable.name} set value {variable.value if variable.type != "string" else stringForm}'
                    if variable.type == "float":
                        text += "f"
                elif variable.type == "entity[]":
                    if len(variable.value) > 0:
                        text = f'#variable "{variable.name}" Initialization index 0'
                        text += f"\ntag {variable.value[0]} add in_{main.packId}_{variable.name}"
                        if len(variable.value) > 1:
                            index = 1
                            for i in variable.value[1:]:
                                text += f"\n#variable \"{variable.name}\" Initialization index {index}\ntag {i} add in_{main.packId}_{variable.name}"
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

                    text = f"tag {variable.value} add {main.packId}_{variable.name}"
        else:
            text = f"#The {variable.modifier} variable \"{variable.name}\" is defined, but has no initializing value."

        super().__init__(text, parentFunction)