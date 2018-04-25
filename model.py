import sys
import time
from urllib.parse import urljoin

class Challenge():
    def __init__(self, c_info):
        self.id = c_info["id"]
        self.rated = c_info["rated"]
        self.variant = c_info["variant"]["key"]
        self.perf_name = c_info["perf"]["name"]
        self.speed = c_info["speed"]
        self.challenger = c_info.get("challenger")
        self.challengerTitle = self.challenger.get("title") if self.challenger else None
        self.challengerMasterTitle = self.challengerTitle if self.challengerTitle != "BOT" else None
        self.challengerName = self.challenger["name"] if self.challenger else "Anonymous"
        self.challengerRatingInt = self.challenger["rating"] if self.challenger else 0
        self.challengerRating = self.challengerRatingInt or "?"

    def is_supported_variant(self, supported):
        return self.variant in supported

    def is_supported_speed(self, supported):
        return self.speed in supported

    def is_supported_mode(self, supported):
        return "rated" in supported if self.rated else "casual" in supported

    def is_supported(self, config):
        variants = config["supported_variants"]
        tc = config["supported_tc"]
        modes = config["supported_modes"]
        return self.is_supported_speed(tc) and self.is_supported_variant(variants) \
            and self.is_supported_mode(modes) and self.is_supported_match(config)

    def score(self):
        ratedBonus = 200 if self.rated else 0
        titledBonus = 200 if self.challengerMasterTitle else 0
        return self.challengerRatingInt + ratedBonus + titledBonus

    def mode(self):
        return "rated" if self.rated else "casual"

    def challengerFullName(self):
        return "{}{}".format(self.challengerTitle + " " if self.challengerTitle else "", self.challengerName)

    def is_supported_match(self, config):
        if "supported_matches" not in config:
            return True
        if self.mode() in config["supported_matches"]:
            if self.challengerTitle == "BOT" and config["supported_matches"][self.mode()] == "bot":
                return True
            if self.challengerTitle != "BOT" and config["supported_matches"][self.mode()] == "human":
                return True
        return False

    def __str__(self):
        return "{} {} challenge from {}({})".format(self.perf_name, self.mode(), self.challengerFullName(), self.challengerRating)

    def __repr__(self):
        return self.__str__()

class Game():
    def __init__(self, json, username, base_url, abort_time):
        self.username = username
        self.id = json.get("id")
        self.speed = json.get("speed")
        clock = json.get("clock", {})
        self.clock_initial = clock.get("initial", 1000 * 3600 * 24 * 365 * 10) # unlimited = 10 years
        self.clock_increment = clock.get("increment", 0)
        self.perf_name = json.get("perf").get("name") if json.get("perf") else "{perf?}"
        self.variant_name = json.get("variant")["name"]
        self.white = Player(json.get("white"))
        self.black = Player(json.get("black"))
        self.initial_fen = json.get("initialFen")
        self.state = json.get("state")
        self.is_white = bool(self.white.name and self.white.name == username)
        self.my_color = "white" if self.is_white else "black"
        self.opponent_color = "black" if self.is_white else "white"
        self.me = self.white if self.is_white else self.black
        self.opponent = self.black if self.is_white else self.white
        self.base_url = base_url
        self.white_starts = self.initial_fen == "startpos" or self.initial_fen.split()[1] == "w"
        self.abort_at = time.time() + abort_time

    def url(self):
        return urljoin(self.base_url, "{}/{}".format(self.id, self.my_color))

    def is_abortable(self):
        return len(self.state["moves"]) < 6

    def abort_in(self, seconds):
        if (self.is_abortable()):
            self.abort_at = time.time() + seconds

    def should_abort_now(self):
        return self.is_abortable() and time.time() > self.abort_at

    def __str__(self):
        return "{} {} vs {}".format(self.url(), self.perf_name, self.opponent.__str__())

    def __repr__(self):
        return self.__str__()


class Player():
    def __init__(self, json):
        self.id = json.get("id")
        self.name = json.get("name")
        self.title = json.get("title")
        self.rating = json.get("rating")
        self.provisional = json.get("provisional")
        self.aiLevel = json.get("aiLevel")

    def __str__(self):
        if self.aiLevel:
            return "AI level {}".format(self.aiLevel)
        else:
            rating = "{}{}".format(self.rating, "?" if self.provisional else "")
            return "{}{}({})".format(self.title + " " if self.title else "", self.name, rating)

    def __repr__(self):
        return self.__str__()
