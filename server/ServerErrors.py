# This file contains symbolic names of all errors
# returned by InfoMan server

# return serverFailure if there was an internal error in the server
# (probably a bug in the server code)
serverFailure = 1
unsupportedDevice = 2
# return malformedRequest if the request sent by a client is
# not recognized by the server (probably a bug in the client code)
malformedRequest = 4
lookupLimitReached = 5
# server returns invalid protocol version if the protocolVersion field
# send by client is not valid (probably a bug in the client)
invalidProtocolVersion = 6
requestArgumentMissing = 7
unexpectedRequestArgument = 8
invalidCookie = 9
userDisabled = 10
invalidRegCode = 11
forceUpgrade = 12
invalidRequest = 13
# we return this if a given module can't return results to a user
# (e.g. because the server we scrap data from is down or for some reason
# returns an error)
moduleTemporarilyDown = 14
# server returns regCodeExpired if a registration term (1 year) for a given
# registration code has expired. The user is then supposed to purchase a new
# registration code
regCodeExpired = 15

# this really isn't an error but just information that server should stop all processing
# until data needed to process the field is available
fieldPending = 1000

# An exception we use to propagate errors
class Error(Exception):
    def __init__(self, code, cause=None):
        self.code=code
        self.cause=cause
        self.args=(code, cause)

