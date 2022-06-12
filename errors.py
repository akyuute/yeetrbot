from argparse import ArgumentError


class BotError(Exception):
    '''Base exception for custom bot errors.'''
    pass

class DatabaseError(BotError):
    '''Base exception for errors that occur in a database transaction.'''
    pass

class RegistrationError(BotError):
    '''Base exception for errors that occur when registering new channels or
    commands and their attributes.'''
    pass

class NotFoundError(BotError):
    '''Base exception for failed object lookups.'''
    pass

class ParsingError(BotError):
    '''Base exception for errors that occur when parsing input.'''
    pass


class NameConflict(RegistrationError): ...
    #'''Error raised when the name of a new object conflicts with that of one
    #which already exists.'''
    #pass


class ChannelNotFoundError(NotFoundError): ...
    #'''Error raised when a channel cannot be identified.'''
    #pass

class CommandNotFoundError(NotFoundError): ...
    #'''Error raised when a custom channel command cannot be identified.'''
    #pass

class VariableNotFoundError(NotFoundError): ...
    #'''Error raised when a custom channel variable cannot be identified.'''
    #pass


class InvalidArgument(ParsingError): ...
    #'''Error raised when a parsed argument is flagged as invalid.'''
    #pass

class InvalidSyntax(ParsingError): ...
    #'''Error raised when the syntax of one or more arguments is invalid.'''
    #pass

class InvalidAction(ParsingError): ...
    #'''Error raised when certain arguments of a command string does not represent a valid action.'''
    #pass

class CommandHelpMessage(Exception): ...

