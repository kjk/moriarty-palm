#ifndef MORIARTY_H_
#define MORIARTY_H_

#include "moriarty_Rsc.h"


#define appFileCreator          'imAN'
#define appName                 "InfoMan"

/* centralize all the strings that depend on the version number so that we
   don't forget update them when we update version number */
#define appVersion             "1.4"
/* this is what we send as our id (clientInfoField) to the server */
#define clientInfo             "Palm 1.4"

#define updateCheckURL          _T("http://www.arslexis.com/updates/palm-infoman-1-4.html")

#define appPrefDatabase appName " Prefs"

#define appDataFile appName " Data"

enum {
    rsaKeyLengthBits = 512,
    rsaKeyLengthBytes = rsaKeyLengthBits / 8
};    


extern const char rsaPublicKey[rsaKeyLengthBytes + 1];

#endif /* MORIARTY_H_ */
