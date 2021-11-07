import os
import json
import tags
import shutil
import re
import sys
import commands
from tools import *
#import convert

packName = "Generated Data Pack"
packId = "generated_data_pack"
packDesc = "Data pack generated from a Minecraft Programming Language compiler"
packShort = "gdp"
defaultPackInfo = False
useSnapshots = False

preinitFunction = commands.Function(
    packId, "internal/preload",
    "It is necessary to delay the load function by 1 second so that it may be run on world load correctly.",
    0)
initFunction = commands.Function(packId, "internal/load",
                        "This function is run when the datapack is loaded.", 0)
uninstallFunction = commands.Function(
    packId, "uninstall",
    "Can be called to remove the pack and any trace it was ever installed", 0)
tickFunction = commands.Function(
    packId, "internal/tick",
    "This function is run every tick after this datapack is loaded.", 0)
customFunctions = {
    "exists":
    commands.Function(packId, "exists",
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
                    function = commands.Function(
                        packId,
                        f"listeners/{name}/{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}{version}",
                        f"This function is called for every {name} event with 0 priority",
                        0)
                else:
                    priority = int(priority)
                    function = commands.Function(
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
                        function = commands.Function(
                            packId,
                            f"{path}{'/' if path != '' else ''}{'.'.join(file.split('.')[:-1])}/{name.replace('.', '_')}",
                            f"The function defined with the name '{name}' in the file '{path}/{file}'",
                            0)
                    else:
                        function = commands.Function(
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
                            commands.Function(
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
                            commands.Variable(packId, name, modifier, t, value, desc,
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
                commands.LiteralCommand(line, function).implement()
            else:
                #Comment
                match = re.match(r'comment((?P<message>.+))(\)$)', line)
                if match != None:
                    message = groups(
                        match.group("message"), [['"', '"', True]], False)[0]
                    commands.Comment(message, function).implement()
                else:
                    #Function call
                    match = re.match(
                        r'(?P<function>[a-z_0-9\.]+(:)?[a-z_0-9\.]+)(?<!\.)\(\)',
                        line)
                    if match != None:
                        f = match.group("function")
                        functionList = f.split(":")
                        if len(functionList) < 2:
                            functionList = f.split(".")
                            if len(functionList) == 1:
                                commands.CallFunction(
                                    f"{packId}:{parentScript}/{functionList[0]}",
                                    function).implement()
                            else:
                                commands.CallFunction(
                                    f"{packId}:{'/'.join(functionList)}",
                                    function).implement()
                        else:
                            namespace = functionList[0]
                            functionList = functionList[1].split(".")
                            commands.CallFunction(
                                f"{namespace}:{'/'.join(functionList)}",
                                function).implement()
                    else:
                        #Execute clause
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
                                wrapper = commands.ExecuteWrapper(
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
        print("Saving the file as a copy in the datapack")
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

    print("Saving main.mcscript as a copy in the datapack")
    os.makedirs(
        f".generated/packs/{packName}/source",
        exist_ok=True)
    shutil.copyfile(
        "main.mcscript",
        f".generated/packs/{packName}/source/main.mcscript"
    )

    print("Populating default function statements")
    commands.Statement(f"schedule function {packId}:{initFunction.name} 1s replace",
              preinitFunction).implement()

    commands.Statement(f"scoreboard objectives add {packShort}_temp dummy",
              initFunction).implement()
    commands.Statement(f"scoreboard objectives remove {packShort}_temp",
              uninstallFunction).implement()
    commands.Statement(f"scoreboard players set {packId} {packShort}_temp 0",
              initFunction).implement()
    #This line is only here so that the variable will register itself as visible to the rest of the program.
    #Initialization and manipulation are covered by other lines.
    commands.Variable(packId, f"{packShort}_temp", "entity", "int", "0",
             f"Temporary score for this pack.", False)
    if playerPreference == "single":
        commands.Statement("", initFunction).implement()
        commands.Comment("Ensure the game is run in singleplayer",
                initFunction).implement()
        commands.Statement(
            f"execute as @a run scoreboard players add {packId} {packShort}_temp 1",
            initFunction).implement()
        commands.Statement(
            f'execute if score {packId} {packShort}_temp matches 2.. run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with singleplayer.\\nDisabling the pack to avoid unexpected behavior.\\nUse "}},{{"text":"/datapack enable \\"file/{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"Click to copy this command to the chat bar."}}]}},"clickEvent":{{"action":"suggest_command","value":"/datapack enable \\"file/{packName}\\""}}}},{{"text":" To reenable."}}]',
            initFunction).implement()
        commands.Statement(
            f'execute if score {packId} {packShort}_temp matches 2.. run datapack disable "file/{packName}"',
            initFunction).implement()
        commands.Statement(
            f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches ..1',
            initFunction).implement()
    elif playerPreference == "multi":
        commands.Statement("", initFunction).implement()
        commands.Comment("Ensure the game is run in multiplayer",
                initFunction).implement()
        commands.Statement(
            f"execute as @a run scoreboard players add {packId} {packShort}_temp 1",
            initFunction).implement()
        commands.Statement(
            f'execute if score {packId} {packShort}_temp matches ..1 run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":" is only compatible with multiplayer.\\nDisabling the pack to avoid unexpected behavior.\\nUse "}},{{"text":"/datapack enable \\"file/{packName}\\"","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"Click to copy this command to the chat bar."}}]}},"clickEvent":{{"action":"suggest_command","value":"/datapack enable \\"file/{packName}\\""}}}},{{"text":" To reenable."}}]',
            initFunction).implement()
        commands.Statement(
            f'execute if score {packId} {packShort}_temp matches ..1 run datapack disable "file/{packName}"',
            initFunction).implement()
        commands.Statement(
            f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches 2..',
            initFunction).implement()

    #Add a new line to the function
    commands.Statement("", initFunction).implement()
    
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

                    print("Saving the file as a copy in the datapack")
                    os.makedirs(
                            f".generated/packs/{packName}/source/{os.path.relpath(subdir)}",
                            exist_ok=True)
                    shutil.copyfile(
                        path,
                        f".generated/packs/{packName}/source/{path}"
                    )
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
                        oldPathList = list(pathList)
                        name = pathList[0]
                        if not name in libraryNamespaces:
                            libraryNamespaces.append(name)
                        if len(pathList) > 2:
                            pathList[0], pathList[1] = pathList[1], pathList[0]
                            p = "/".join(pathList[1:-1]
                                         ) + "/" + pathList[-1].split(".")[0]
                            if pathList[0] == "functions" and pathList[
                                    -1].endswith(".mcfunction"):
                                customFunctions[p] = commands.Function(
                                    packId, p, "Imported from a library", 0)

                        pathList = pathList[:-1]
                        oldPathList = oldPathList[:-1]
                        os.makedirs(
                            f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}",
                            exist_ok=True)
                        shutil.copyfile(
                            path,
                            f".generated/packs/{packName}/data/{packId}/{'/'.join(pathList)}/{file}"
                        )
                        print("Saving to the datapack as a copy")
                        os.makedirs(
                            f".generated/packs/{packName}/source/#{'/'.join(oldPathList)}",
                            exist_ok=True)
                        shutil.copyfile(
                            path,
                            f".generated/packs/{packName}/source/#{'/'.join(oldPathList)}/{file}"
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

                        print("Saving the file as a copy in the datapack")
                        os.makedirs(
                                f".generated/packs/{packName}/source/{os.path.relpath(subdir)}",
                                exist_ok=True)
                        shutil.copyfile(
                            path,
                            f".generated/packs/{packName}/source/{path}"
                        )

    for name in libraryNamespaces:
        libraries.append(name)
        print(f'updating namespace calls from "{name}" to "{packId}:{name}/"')
        for path in libraryFiles:
            update_namespace(path, packId, name)

    print("Requiring packs")
    if len(requiredPacks) > 0:
        commands.Comment("Ensure all required packs are installed.",
                initFunction).implement()
        for pack in requiredPacks:
            commands.Statement(
                f"execute if data storage {packId} {{isCompatible:1}} store success score {packId} {packShort}_temp run function {pack}:exists",
                initFunction).implement()
            commands.Statement(
                f'execute if score {packId} {packShort}_temp matches 0 run tellraw @a {{"text":"The required pack \"{pack}\" was not detected to exist.\\n Disabling to avoid unexpected behavior.","color":"red"}}',
                initFunction).implement()
            commands.Statement(
                f'execute if score {packId} {packShort}_temp matches 0 run datapack disable "file/{packName}"',
                initFunction).implement()
            commands.Statement(
                f'execute store success storage {packId} isCompatible int 1 if score {packId} {packShort}_temp matches 1',
                initFunction).implement()
            commands.Statement("", initFunction).implement()

    print("Setting up listener calls")
    for key in listeners:
        if not key in internalListeners:
            scoresToReset = []
            listeners[key].sort(key=lambda x: x.priority)
            for function in listeners[key]:
                if not function.scoreId in variables:
                    commands.Comment(f"Used for listener {function.listenerId}",
                            initFunction).implement()
                    commands.Statement(
                        f'scoreboard objectives add {function.scoreId[:min([len(function.scoreId), 16])]} {function.listenerId}',
                        initFunction).implement()
                    #This line is only here so that the variable will register itself as visible to the rest of the program.
                    #Initialization and manipulation are covered by other lines.
                    commands.Variable(packId, function.scoreId, "entity", "int", "0",
                             f"Used for listener {function.listenerId}", False)

                commands.Statement("", tickFunction).implement()
                commands.Comment("Run listeners", tickFunction).implement()
                commands.Statement(
                    f'execute as @e[scores={{{function.scoreId[:min([len(function.scoreId), 16])]}=1..}}] at @s run function {function.namespace}:{function.name}',
                    tickFunction).implement()
                scoresToReset.append(
                    function.scoreId[:min([len(function.scoreId), 16])])

            if len(scoresToReset) > 0:
                commands.Statement("", tickFunction).implement()
                commands.Comment("Reset listener scores", tickFunction).implement()
            for score in scoresToReset:
                #Reset the score
                commands.Statement(f"scoreboard players set @e {score} 0",
                          tickFunction).implement()
                #Remove the score on uninstall
                commands.Statement(f"scoreboard objectives remove {score}",
                          uninstallFunction).implement()

    if "tick" in listeners:
        #Add a new line to the function
        commands.Statement("", tickFunction).implement()
        commands.Comment("Run tick listeners", tickFunction).implement()
        listeners["tick"].sort(key=lambda x: x.priority)
        for function in listeners["tick"]:
            commands.Statement(f"function {function.namespace}:{function.name}",
                      tickFunction).implement()
    if "load" in listeners:
        #Add a new line to the function
        commands.Statement("", initFunction).implement()
        commands.Comment("Run listeners", initFunction).implement()
        listeners["load"].sort(key=lambda x: x.priority)
        for function in listeners["load"]:
            commands.Statement(f"function {function.namespace}:{function.name}",
                      initFunction).implement()
    if "uninstall" in listeners:
        #Add a new line to the function
        commands.Statement("", uninstallFunction).implement()
        commands.Comment("Run listeners", uninstallFunction).implement()
        listeners["uninstall"].sort(key=lambda x: x.priority)
        for function in listeners["uninstall"]:
            commands.Statement(f"function {function.namespace}:{function.name}",
                      uninstallFunction).implement()
    if "spawn" in listeners:
        #Add a new line to the function
        commands.Statement("", tickFunction).implement()
        commands.Comment("Run spawn listeners", tickFunction).implement()
        listeners["spawn"].sort(key=lambda x: x.priority)
        for function in listeners["spawn"]:
            commands.Statement(
                f"execute as @e[tag=!{packId}_spawned] at @s run function {function.namespace}:{function.name}",
                tickFunction).implement()

    #The "spawned" tag will be used by some other parts of the generator.
    commands.Statement(f"tag @e[tag=!{packId}_spawned] add {packId}_spawned",
              tickFunction).implement()

    print('Adding "datapack loaded/unloaded" notification')
    #Add a new line to the function
    commands.Statement("", initFunction).implement()
    commands.Comment("Uninstall if incompatible", initFunction).implement()
    initFunction.append(
        f'execute if data storage {packId} {{isCompatible:1}} run tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully (re)loaded."}}]'
    )
    commands.Comment("Uninstall the pack if it is incompatible",
            initFunction).implement()
    commands.Statement(
        f"execute if data storage {packId} {{isCompatible:0}} run function {packId}:{uninstallFunction.name}",
        initFunction).implement()

    for lib in libraries:
        uninstallFunction.append(f'function {packId}:{lib}/uninstall')
    #Add a new line to the function
    commands.Statement("", uninstallFunction).implement()
    uninstallFunction.append(
        f'tellraw @a [{{"text":"The pack "}},{{"text":"\\"{packName}\\" ","color":"green","hoverEvent":{{"action":"show_text","contents":[{{"text":"{packId} - {packShort}\\n{packDesc}"}}]}}}},{{"text":"has been sucessfully unloaded."}}]'
    )
    commands.Statement(f'datapack disable "file/{packName}"',
              uninstallFunction).implement()
    commands.Statement("", initFunction).implement()
    commands.Comment("Start the tick function", initFunction).implement()
    commands.Statement(
        f"execute if score {packId} {packShort}_temp matches 1 run function {packId}:{tickFunction.name}",
        initFunction).implement()
    commands.Statement("", tickFunction).implement()
    commands.Comment("Start the tick function again next tick",
            tickFunction).implement()
    commands.Statement(f"schedule function {packId}:{tickFunction.name} 1t replace",
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
                f"commands.Function \"{customFunctions[i].namespace}:{customFunctions[i].name}\" is defined. Adding it to the data."
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
