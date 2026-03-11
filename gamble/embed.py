class SixEmbed:
    def __init__(self, choice: list[int]):
        self.choice = choice

    def message(self):
        resp = ""
        for c in range(3):
            for r in range(3):
                resp += ":red_circle:" if (c * 3 + r) in self.choice else ":o:"
            resp += "\n"
        return resp
