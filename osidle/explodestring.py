def rangeString(b, e):
    if ord(b) > ord(e): return None
    return "".join([ chr(x) for x in range(ord(b), ord(e) + 1) ])

class RangeExploder:    
    START_CHAR = list(rangeString("a", "z") + rangeString("A", "Z") + "_")
    INSIDE_CHAR = list(rangeString("a", "z") + rangeString("A", "Z") + "_" + rangeString("0", "9"))
    RANGE_START = list("[")
    RANGE_END = list("]")
    NUMBER = list(rangeString("0", "9"))
    RANGE_RANGE = list("-")
    RANGE_SPLIT = list(",")
    BLANKS = list(" \t\r\n")
    NAME_END = [ "," ]
    EOF = [ None ]

    def __init__(self) -> None:
        self._c = None
        self._p = 0
        self._s = ""

    def _next(self):
        if (self._p >= len(self._s)):
            self._c = None
            return None
        self._c = self._s[self._p]
        self._p = self._p + 1

    def _begin(self, s):
        self._c = None
        self._p = 0
        self._s = s
        self._next()

    def _raiseError(self, info = None):
        infostr = "" if info is None else f" invalid {info} "
        raise Exception(f"error: {infostr}{self._s} at {self._p}") 

    def _parseName(self):
        if self._c not in self.START_CHAR:
            self._raiseError("name")
        names = []
        while True:
            result = ""
            while self._c in self.INSIDE_CHAR:
                result = result + self._c
                self._next()
            if result != "":
                # The first time result is not ""
                if len(names) == 0:
                    names = [ result ]
                else:
                    names = list(map(lambda x: x + result, names))
            if self._c in self.RANGE_START:
                range = self._parseRange()
                explodedNames = []
                for name in names:
                    for i in range:
                        explodedNames.append(name + str(i))
                names = explodedNames                        
            if self._c in self.NAME_END + self.EOF:
                break
        return names

    def _parseNumber(self):
        if self._c not in self.NUMBER:
            self._raiseError("number")
        result = ""
        while self._c in self.NUMBER:
            result = result + self._c
            self._next()
        return int(result)

    def _parseRange(self):
        if self._c not in self.RANGE_START:
            self._raiseError("range")
        self._next()
        while self._c in self.BLANKS:
            self._next()

        values = []

        while True:
            start = self._parseNumber()
            if self._c in self.RANGE_RANGE:
                self._next()
                end = self._parseNumber()
                values = values + list(range(start, end + 1))
            else:
                values = values + [ start ]
            if self._c not in self.RANGE_SPLIT:
                break
            self._next()

        if self._c not in self.RANGE_END:
            self._raiseError("range")

        self._next()

        return values

    def parse(self, name):
        self._begin(name)
        names = []
        while True:
            while self._c in self.BLANKS:
                self._next()
            if self._c in self.EOF:
                break
            names = names + self._parseName()
            if self._c in self.EOF:
                break
            elif self._c in self.NAME_END:
                self._next()
            else:
                self._raiseError("name")
        return names

if __name__ == "__main__":
    print(rangeString("a", "z") + rangeString("A", "Z") + "_")
    r = RangeExploder()
    r.parse("torito0[1-5,6,7], torito02, torito03, torito04")