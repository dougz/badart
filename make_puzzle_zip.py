#!/usr/bin/python3

import os
import zipfile

with zipfile.ZipFile("badart.zip", mode="w") as z:
  with z.open("puzzle.html", "w") as f_out:
    with open("badart.html", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("solution.html", "w") as f_out:
    with open("solution.html", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("metadata.cfg", "w") as f_out:
    with open("metadata.cfg", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("badart.css", "w") as f_out:
    with open("badart.css", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("badart.js", "w") as f_out:
    with open("badart.js", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("tada.wav", "w") as f_out:
    with open("tada.wav", "rb") as f_in:
      f_out.write(f_in.read())

  for i in range(1, 13):
    path = f"images/{i:02d}"
    for fn in os.listdir(path):
      with z.open(f"{i:02d}/{fn}", "w") as f_out:
        with open(os.path.join(path, fn), "rb") as f_in:
          f_out.write(f_in.read())






