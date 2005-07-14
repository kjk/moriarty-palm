#include "MoviesData.hpp"
#include <set>
#include <map>
#include <Utility.hpp>
#include <UniversalDataFormat.hpp>

#ifdef __MWERKS__
# pragma far_code
#endif

TheatreByMovie::TheatreByMovie(const ArsLexis::String& aName, const ArsLexis::String& anAddress, const ArsLexis::String& theHours): 
    name(aName), address(anAddress), hours(theHours) {}

TheatreByMovie::TheatreByMovie() {}

TheatreByMovie::~TheatreByMovie() {}

Movie::Movie(const ArsLexis::String& aTitle): title(aTitle) {}

Movie::Movie() {}

Movie::~Movie() 
{
    std::for_each(theatres.begin(), theatres.end(), ObjectDeleter<TheatreByMovie>());
}

struct TheatreNameLess {
    bool operator()(const TheatreByMovie* t0, const TheatreByMovie* t1) const
    {return t0->name<t1->name;}
};

static void doCreateMoviesFromTheatres(Movies_t& out, const UniversalDataFormat& in)
{
    typedef std::set<TheatreByMovie*, TheatreNameLess> TheatresByMovieSet;
    typedef std::map<String, TheatresByMovieSet> MoviesMap;
    MoviesMap moviesMap;
    uint_t theatresCount = in.getItemsCount()/2;
    for (uint_t i = 0; i < theatresCount; ++i)
    {
        const uint_t theatreRow = i*2;
        const uint_t moviesRow = theatreRow + 1;
        const String theatreName = in.getItemText(theatreRow, theatreNameIndex);
        const String theatreAddress = in.getItemText(theatreRow, theatreAddressIndex);
        uint_t moviesCount = in.getItemElementsCount(moviesRow)/2;
        for (uint_t m = 0; m<moviesCount; ++m)
        {
            const String movieTitle = in.getItemText(moviesRow, m*2);
            const String movieHours = in.getItemText(moviesRow, m*2+1);
            moviesMap[movieTitle].insert(new TheatreByMovie(theatreName, theatreAddress, movieHours));
        }
    }
    MoviesMap::const_iterator mmend=moviesMap.end();
    for (MoviesMap::const_iterator mmit=moviesMap.begin(); mmit!=mmend; ++mmit)
    {
        out.push_back(new Movie((*mmit).first));
        std::copy((*mmit).second.begin(), (*mmit).second.end(), std::back_inserter(out.back()->theatres));
    }
}

ArsLexis::status_t createMoviesFromTheatres(Movies_t& out, const UniversalDataFormat& in)
{
    volatile ArsLexis::status_t error=errNone;
    ErrTry {
        doCreateMoviesFromTheatres(out, in);
    }
    ErrCatch(ex) {
        error=ex;
    } ErrEndCatch
    return error;
}
