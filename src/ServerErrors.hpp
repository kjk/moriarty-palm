// This file defines errors returned by a server
// We put all the info related to server errors here in one place so that
// we don't forget to update related things
// In order to use this data clients are supposed to do the following trick:
// #undef DEF_SERVER_ERR
// #define DEF_SERVER_ERR(error, code, alert) \ <- apropriate macro
// #include ServerErrors.hpp
// This is also a reason we don't put #ifndef guards - this include file
// is supposed to be included multiple times
// error is a symbolic name (enum ServerError)
// code corresponds to the numeric value of the error as returned from server
//      (defined in ServerErrors.py)
// alert is the alert id we display on the client for this error
DEF_SERVER_ERR(serverErrorNone,0,unknownServerErrorAlert)
DEF_SERVER_ERR(serverErrorFailure,1,serverFailureAlert)
DEF_SERVER_ERR(serverErrorUnsupportedDevice,2,unsupportedDeviceAlert)
DEF_SERVER_ERR(serverErrorMalformedRequest,4,malformedRequestAlert)
DEF_SERVER_ERR(serverErrorLookupLimitReached,5,lookupLimitReachedAlert)
DEF_SERVER_ERR(serverErrorInvalidProtocolVersion,6,invalidProtocolVersionAlert)
DEF_SERVER_ERR(serverErrorRequestArgumentMissing,7,requestArgumentMissingAlert)
DEF_SERVER_ERR(serverErrorUnexpectedRequestArgument,8,unexpectedRequestArgumentAlert)
DEF_SERVER_ERR(serverErrorInvalidCookie,9,invalidCookieAlert)
DEF_SERVER_ERR(serverErrorUserDisabled,10,userDisabledAlert)
DEF_SERVER_ERR(serverErrorInvalidRegCode,11,invalidRegCodeAlert)
DEF_SERVER_ERR(serverErrorForceUpgrade,12,forceUpgradeAlert)
DEF_SERVER_ERR(serverErrorInvalidRequest,13,invalidRequestAlert)
DEF_SERVER_ERR(serverErrorModuleTemporarilyDown,14,moduleTemporarilyDownAlert)
DEF_SERVER_ERR(serverErrorRegCodeExpired,15,serverFailureAlert)

