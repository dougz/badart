#!/usr/bin/python3

import argparse
import os
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
options = parser.parse_args()

with zipfile.ZipFile("gallery_of_tomorrow.zip", mode="w") as z:
  with z.open("puzzle.html", "w") as f_out:
    with open("badart.html", "rb") as f_in:

      html = f_in.read()

      if options.debug:
        head = ('<link rel=stylesheet href="/artdebug/badart.css" />'
                '<script src="/closure/goog/base.js"></script>'
                '<script src="/artdebug/badart.js"></script>')
      else:
        head = ('<link rel=stylesheet href="badart.css" />'
                '<script src="badart-compiled.js"></script>')

      html = html.replace(b"@HEAD@", head.encode("utf-8"))

      f_out.write(html)

  with z.open("solution.html", "w") as f_out:
    with open("solution.html", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("for_ops.html", "w") as f_out:
    with open("for_ops.html", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("metadata.yaml", "w") as f_out:
    with open("metadata.yaml", "rb") as f_in:
      f_out.write(f_in.read())

  if not options.debug:
    with z.open("badart.css", "w") as f_out:
      with open("badart.css", "rb") as f_in:
        f_out.write(f_in.read())

    with z.open("badart-compiled.js", "w") as f_out:
      with open("badart-compiled.js", "rb") as f_in:
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






