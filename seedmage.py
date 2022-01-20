import argparse
import random
import time, sys

import torrent
import utils

import os

f_list = os.listdir('./torrent')
seeder_list = list()
for i in f_list:
    if os.path.splitext(i)[1] == '.torrent':
      torrent_file = torrent.File('./torrent/' + i)
      print("Torrent:")
      print(torrent_file)

      seeder = torrent.Seeder(torrent_file)
      seeder.load_peers()
      print("Seeder:")
      print(seeder)
      seeder_list.append(seeder)

while True:
  try:
    time.sleep(1800)
    for seeder in seeder_list:
      seeder.upload()
      time.sleep(30)
  except KeyboardInterrupt:
    for seeder in seeder_list:
      seeder.stop()
      time.sleep(1)
    print("Bye!")
    sys.exit()
