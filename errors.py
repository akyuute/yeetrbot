from argparse import ArgumentError


class BotError(Exception):
    '''Base exception for custom bot errors.'''
    pass

class DatabaseError(BotError):
    '''Exception raised for errors in a database transaction.'''
    pass

class AssignmentError(BotError):
    '''Base exception for errors in attribute assignment operations.'''
    # def __init__(self, attr, message=None):
        # self.attr = attr
        # if message is not None:
            # super.__init__(self, message)
        # else:
            # super.__init__(self, )
    pass

class RegistrationError(AssignmentError):
    '''Exception raised for errors in registering channel attributes.'''
    pass

class ChannelNotFoundError(AssignmentError):
    '''Exception raised when a channel cannot be found.'''
    pass

class CommandNotFoundError(AssignmentError):
    '''Exception raised when a command cannot be found.'''
    pass

class VariableNotFoundError(AssignmentError):
    '''Exception raised when a variable cannot be found.'''
    pass

class NameConflict(AssignmentError):
    '''Exception raised when one attribute name conflicts with another.'''
    pass


class ParsingError(Exception):
    '''Base exception for parsing errors.'''

class InvalidArgument(ParsingError):
    '''Error raised when a parsed argument is counted as invalid.'''
    pass

class InvalidSyntax(ParsingError):
    '''Error raised when the syntax of a series of arguments is invalid.'''
    pass

class InvalidAction(ParsingError):
    '''Error raised when the first argument of a
    command string does not match a valid action.'''
    pass
