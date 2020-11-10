import main
import csv
import os
import math

def numberCast(i):
  try:
    return float(i)
  except:
    return -math.inf

def start():
  print("Creating necessary file paths")
  os.makedirs("saved/tags/blocks", exist_ok = True)
  os.makedirs("saved/tags/entities", exist_ok = True)
  os.makedirs("saved/tags/items", exist_ok = True)
  os.makedirs("saved/tags/functions", exist_ok = True)

  print("looking for mctag files")
  for file in os.listdir(os.getcwd()):
    if file.endswith(".mctag") and not file == "main.mcscript":
      print(f"found file \"{file}\"")
      code = []
      options = []

      with open(file) as data:
        for i in data:
          code.append(i)
      
      print("contents:")
      code = main.noComments(code)
      for i in range(0,len(code)):
        code[i] = code[i].replace(" ", "")
        print(f"\t{i}: {code[i]}")

      type = main.words(":", code[0], [['"','"']], False, False)[1]
      print(f'type is "{type}"')
      print(f'Loading "{type}.csv" into memory')

      with open(f"saved/data/{type}.csv", "r") as csvFile:
        dictReader = csv.DictReader(csvFile)
        for i in dictReader:
          options.append(i)
      print(f'got {len(options)} entries from "{type}.csv"')

      for line in code[1:]:
        #TODO: Add entries based on code here
        pass

      print(f'deleting "{type}.csv" from memory to save space')
      del options
if __name__ == "__main__":
  start()