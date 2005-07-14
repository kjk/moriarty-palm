#ifndef __MORIARTY_MOVIES_DATA_HPP__
#define __MORIARTY_MOVIES_DATA_HPP__

#include <Debug.hpp>
#include <BaseTypes.hpp>
#include <vector>

class UniversalDataFormat;

enum {
    theatreNameIndex,
    theatreAddressIndex,
    theatreTupleItemsCount
};

struct TheatreByMovie
{
    ArsLexis::String name;
    ArsLexis::String address;
    ArsLexis::String hours;
            
    TheatreByMovie(const ArsLexis::String& aName, const ArsLexis::String& anAddress, const ArsLexis::String& theHours);
    
    TheatreByMovie();
    
    ~TheatreByMovie();
};

struct Movie
{
    ArsLexis::String title;
    typedef std::vector<TheatreByMovie*> TheatresByMovie_t;
    TheatresByMovie_t theatres;
    
    Movie(const ArsLexis::String& aTitle);
    
    Movie();
    
    ~Movie();
};

typedef std::vector<Movie*> Movies_t;

ArsLexis::status_t createMoviesFromTheatres(Movies_t& out, const UniversalDataFormat& in);

#endif