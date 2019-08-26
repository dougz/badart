#!/usr/bin/python3

import argparse
import asyncio
import json
import os
import time
import unicodedata

import http.client
import tornado.web

import scrum


class Image:
  def __init__(self, url, width):
    self.url = url
    self.width = width
    self.last = False

class Painting:
  BY_NAME = {}

  ORDERED_IMAGES = []

  @classmethod
  def set_options(cls, options):
    cls.options = options

  def __init__(self, title, answers, image_dir):
    self.title = title  # with "Bad"

    self.answers = []
    for a in answers:
      self.answers.append(a)
      if a.startswith("THE"):
        self.answers.append("THEBAD" + a[3:])
      else:
        self.answers.append("BAD" + a)

    self.images = []
    self.solved = False

    images = [i for i in self.options.assets.keys()
              if i.startswith(image_dir+"/") and i.endswith(".png")]
    images.sort()

    for im in images:
      self.images.append(Image(self.options.assets[im], 800))
      self.ORDERED_IMAGES.append(self.images[-1].url)

    self.images[-1].last = True

class Message:
  def __init__(self, serial, message):
    self.serial = serial
    self.timestamp = time.time()
    self.message = message

class GameState:
  BY_TEAM = {}

  FRAME_SECS = 1.5
  LAST_SECS = 4.0
  INITIAL_OPENING_TIME = 600  # 10 minutes
  CLOSURE_TIME = 1800  # 30 minutes

  @classmethod
  def set_globals(cls, paintings, preload, options):
    cls.paintings = paintings
    cls.preload = preload
    cls.options = options

  @classmethod
  def get_for_team(cls, team):
    if team not in cls.BY_TEAM:
      cls.BY_TEAM[team] = cls(team)
    return cls.BY_TEAM[team]

  def __init__(self, team):
    self.team = team
    self.sessions = set()
    self.running = False
    self.cond = asyncio.Condition()
    self.current_painting = None
    self.open_requested = False

  async def on_wait(self, session):
    async with self.cond:
      if session not in self.sessions:
        self.sessions.add(session)
        self.cond.notify_all()

  async def run_game(self):
    while not self.open_requested:
      count = len(self.sessions)
      text = (f"{count} player{' is' if count == 1 else 's are'} currently waiting.<br>"
              f"You can enter the gallery when there are {self.options.min_players}.")

      if len(self.sessions) < self.options.min_players:
        msg = {"method": "show_message", "text": text}
      else:
        msg = {"method": "prompt_open", "text": text}

      await self.team.send_messages([msg], sticky=1)
      async with self.cond:
        await self.cond.wait()

    now = time.time()
    close_time = now + self.INITIAL_OPENING_TIME
    reopen_time = close_time + self.CLOSURE_TIME
    state = "initial_open"

    while True:
      just_solved = False
      for p in self.paintings:
        self.current_painting = p
        while True:
          next_painting = True
          if p.solved:
            to_show = p.images[-1:]
          else:
            to_show = p.images

          for i in to_show:

            if state == "initial_open" and time.time() > close_time:
              state = "closed"
              d = {"method": "show_message",
                   "text": "The gallery is now closed.<br>It will reopen in 30 minutes.",
                   "end_time": reopen_time,
                   "countdown_text": "The gallery will reopen in"}
              await self.team.send_messages([d], sticky=1)
              await asyncio.sleep(reopen_time - time.time())
              close_time = None
              state = "reopened"

            d = {"method": "show_image",
                 "image": i.url,
                 "preload": self.preload[i.url],
                 "width": str(i.width) + "px",
            }
            if close_time:
              d["end_time"] = close_time
            if p.solved:
              d["title"] = p.title

            if just_solved:
              to_send = [{"method": "play_audio",
                          "url": self.options.assets["tada.wav"]}, d]
              just_solved = False
            else:
              to_send = [d]
            await self.team.send_messages(to_send, sticky=1)

            delay = self.LAST_SECS if i.last else self.FRAME_SECS
            async with self.cond:
              was_solved = p.solved
              try:
                await asyncio.wait_for(self.cond.wait(), delay)
              except asyncio.TimeoutError:
                pass    # next image in current painting
              else:
                if p.solved and not was_solved:
                  # restart current painting to show solved state
                  just_solved = True
                  next_painting = False
                  break

          if next_painting: break




  async def send_chat(self, text):
    d = {"method": "add_chat", "text": text}
    await self.team.send_messages([d])

  async def try_answer(self, answer):
    async with self.cond:
      if (not self.current_painting.solved and
          answer in self.current_painting.answers):
        self.current_painting.solved = True
        self.cond.notify_all()

  async def request_open(self):
    async with self.cond:
      self.open_requested = True
      self.cond.notify_all()


class BadArtApp(scrum.ScrumApp):
  async def on_wait(self, team, session):
    gs = GameState.get_for_team(team)

    if not gs.running:
      gs.running = True
      self.add_callback(gs.run_game)

    await gs.on_wait(session)


class SubmitHandler(tornado.web.RequestHandler):
  def prepare(self):
    self.args = json.loads(self.request.body)

  @staticmethod
  def canonicalize_answer(text):
    text = unicodedata.normalize("NFD", text.upper())
    out = []
    for k in text:
      cat = unicodedata.category(k)
      # Letters and "other symbols".
      if cat == "So" or cat == "Nd" or cat[0] == "L":
        out.append(k)
    return "".join(out)

  async def post(self):
    scrum_app = self.application.settings["scrum_app"]
    team, session = await scrum_app.check_cookie(self)
    gs = GameState.get_for_team(team)

    submission = self.args["answer"]
    answer = self.canonicalize_answer(submission)
    who = self.args["who"].strip()
    if not who: who = "anonymous"
    print(f"{team}: {who} submitted {answer}")

    await gs.send_chat(f"{who} guessed \"{submission}\"")
    await gs.try_answer(answer)

    self.set_status(http.client.NO_CONTENT.value)


class OpenHandler(tornado.web.RequestHandler):
  async def get(self):
    scrum_app = self.application.settings["scrum_app"]
    team, session = await scrum_app.check_cookie(self)
    gs = GameState.get_for_team(team)
    await gs.request_open()
    self.set_status(http.client.NO_CONTENT.value)


class DebugHandler(tornado.web.RequestHandler):
  def get(self, fn):
    if fn.endswith(".css"):
      self.set_header("Content-Type", "text/css")
    elif fn.endswith(".js"):
      self.set_header("Content-Type", "application/javascript")
    with open(fn) as f:
      self.write(f.read())


def make_app(options):
  Painting.set_options(options)

  paintings = [
    Painting("Bad Flag (Moratorium)", {"FLAGMORATORIUM"}, "01"),
    Painting("Bad Irises", {"IRISES"}, "02"),
    Painting("Bad Nighthawks", {"NIGHTHAWKS"}, "03"),
    Painting("Bad Guernica", {"GUERNICA"}, "04"),
    Painting("The Bad Emperor Napoleon in His Study at the Tuileries",
             {"THEEMPERORNAPOLEONINHISSTUDYATTHETUILERIES",
              "EMPERORNAPOLEONINHISSTUDYATTHETUILERIES"},
             "05"),
    Painting("The Bad Raft of the Medusa",
             {"THERAFTOFTHEMEDUSA",
              "RAFTOFTHEMEDUSA",
              "RAFTOFMEDUSA"},
             "06"),
    Painting("The Bad Persistence of Memory",
             {"THEPERSISTENCEOFMEMORY",
              "PERSISTENCEOFMEMORY"},
             "07"),
    Painting("The Bad Arnolfini Portrait",
             {"ARNOLFINIPORTRAIT",
              "THEARNOLFINIPORTRAIT",
              "ARNOLFINIWEDDING",
              "THEARNOLFINIWEDDING",
              "ARNOLFINIMARRIAGE",
              "THEARNOLFINIMARRIAGE"},
             "08"),
    Painting("Bad Impression, Sunrise",
             {"IMPRESSIONSUNRISE"},
             "09"),
    Painting("The Bad Night Watch",
             {"THENIGHTWATCH",
              "NIGHTWATCH"},
             "10"),
    Painting("The Bad Third of May 1808",
             {"THETHIRDOFMAY1808",
              "THIRDOFMAY1808"},
             "11"),
    Painting("The Bad Son of Man",
             {"THESONOFMAN", "SONOFMAN"},
             "12"),
  ]

  preload = {}
  oi = Painting.ORDERED_IMAGES
  for i, u in enumerate(oi):
    preload[u] = oi[(i+1)%len(oi)]

  GameState.set_globals(paintings, preload, options)

  handlers = [
    (r"/artsubmit", SubmitHandler),
    (r"/artopen", OpenHandler),
    (r"/artdebug/(\S+)", DebugHandler),
  ]

  return handlers


def main():
  parser = argparse.ArgumentParser(description="Run the bad art puzzle.")
  parser.add_argument("--assets_json", default=None,
                      help="JSON file for image assets")
  parser.add_argument("-c", "--cookie_secret",
                      default="snellen2020",
                      help="Secret used to create session cookies.")
  parser.add_argument("--socket_path", default="/tmp/badart",
                      help="Socket for requests from frontend.")
  parser.add_argument("--wait_url", default="artwait",
                      help="Path for wait requests from frontend.")
  parser.add_argument("--main_server_port", type=int, default=2020,
                      help="Port to use for requests to main server.")
  parser.add_argument("--min_players", type=int, default=1,
                      help="Number of players needed to start game.")

  options = parser.parse_args()

  assert options.assets_json
  with open(options.assets_json) as f:
    options.assets = json.load(f)

  app = BadArtApp(options, make_app(options))
  app.start()


if __name__ == "__main__":
  main()

