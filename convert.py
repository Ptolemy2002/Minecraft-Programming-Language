import json
import csv
import main

def start():
  with open("convertcsv.csv", "r") as file:
    reader = csv.DictReader(file)
    for i in reader:
      with open(f".saved/tags/items/minecraft:{i['Tag name']}", "w+") as file:
        file.write(i["Values"])
