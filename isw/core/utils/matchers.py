class StringMatcher:
    def __eq__(self, other):
        return isinstance(other, str)
