class ParserError(Exception):
    pass


class URLFetchError(ParserError):
    pass


class URLParseError(ParserError):
    pass


class RecipeExtractionError(ParserError):
    pass
