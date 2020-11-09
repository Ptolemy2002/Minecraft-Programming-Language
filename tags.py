import main
import os

def start():
  print("Creating necessary file paths")
  os.makedirs("saved/tags/blocks", exist_ok = True)
  os.makedirs("saved/tags/entities", exist_ok = True)
  os.makedirs("saved/tags/items", exist_ok = True)
  os.makedirs("saved/tags/functions", exist_ok = True)

if __name__ == "__main__":
  start()