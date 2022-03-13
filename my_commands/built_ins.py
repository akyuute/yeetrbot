# from twitchio.ext import commands

def uptime(perms='everyone'):
    '''Returns the channel uptime in {format}.'''
    print(perms)
    pass

class UniversalCommands:
    default_perms = 'everyone'

    @staticmethod
    def uptime(perms=default_perms):
        '''Returns the channel uptime in {format}.'''
        print(perms)
        pass

if __name__ == '__main__':
    UniversalCommands.uptime()

    pass