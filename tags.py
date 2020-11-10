import main
import csv
import os

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
      
      type = main.words(":", code[0], [], False, False)[1].strip()
      print(f'type is "{type}"')
      print(f'Loading "{type}.csv" into memory')
      with open(f"saved/data/{type}.csv", "r") as csvFile:
        dictReader = csv.DictReader(csvFile)
        for i in dictReader:
          options.append(i)
      print(f'got {len(options)} entries from "{type}.csv"')

      for i in code[1:]:
        pass

      print(f'deleting "{type}.csv" from memory to save space')
      del options
if __name__ == "__main__":
  start()