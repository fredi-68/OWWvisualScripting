
class WindowError(Exception):

    """
    Base exception for errors thrown by the window framework.
    Idealy, this could be used to catch every error raised by this library.
    This does not include errors raised by the underlying graphics backend. 
    """

    pass