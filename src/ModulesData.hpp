#ifndef MORIARTY_MODULES_DATA_HPP__
#define MORIARTY_MODULES_DATA_HPP__

#include <Debug.hpp>
#include <BaseTypes.hpp>
#include <UniversalDataFormat.hpp>

class MoriartyApplication;

#define dataStreamPostfix        _T("data")
#define prefsStreamPostfix       _T("prefs")

#define globalPrefsStream prefsStreamPostfix

#define moviesModulePrefix       _T("movies-")
#define moviesDataStream  moviesModulePrefix dataStreamPostfix
#define moviesPrefsStream moviesModulePrefix prefsStreamPostfix

#define weatherModulePrefix      _T("weather-")
#define weatherDataStream  weatherModulePrefix dataStreamPostfix
#define weatherPrefsStream weatherModulePrefix prefsStreamPostfix

#define m411ModulePrefix         _T("411-")
#define m411DataStream  m411ModulePrefix dataStreamPostfix
#define m411PrefsStream m411ModulePrefix prefsStreamPostfix

#define m411PersonDataStream   m411ModulePrefix _T("person-")   dataStreamPostfix
#define m411BusinessDataStream m411ModulePrefix _T("business-") dataStreamPostfix

#define epicuriousModulePrefix                             _T("recipes-")
#define epicuriousRecipesListStream epicuriousModulePrefix _T("recipesList")
#define epicuriousRecipeStream epicuriousModulePrefix      _T("recipe")
#define epicuriousPrefsStream epicuriousModulePrefix prefsStreamPostfix

#define boxOfficeModulePrefix                  _T("boxOffice-")
#define boxOfficeDataStream boxOfficeModulePrefix dataStreamPostfix

#define currencyModulePrefix                   _T("currency-")
#define currencyDataStream currencyModulePrefix dataStreamPostfix

#define dreamsModulePrefix                     _T("dreams-")
#define dreamsDataStream dreamsModulePrefix dataStreamPostfix

#define horoscopeModulePrefix                  _T("horoscope-")
#define horoscopeDataStream horoscopeModulePrefix dataStreamPostfix

#define jokesModulePrefix                      _T("jokes-")
#define jokesJokesListStream jokesModulePrefix _T("jokesList")
#define jokesJokeStream      jokesModulePrefix _T("joke")

#define stocksModulePrefix                        _T("stocks-")
#define stocksStocksListStream stocksModulePrefix _T("stocksList")

#define gasPricesModulePrefix                 _T("gasPrices-")
#define gasPricesStream gasPricesModulePrefix dataStreamPostfix

#define amazonModulePrefix                        _T("amazon-")
#define amazonHistoryCacheName amazonModulePrefix _T("HistoryCache")
#define amazonModuleName                        _T("Amazon")

#define netflixModulePrefix                         _T("netflix-")
#define netflixHistoryCacheName netflixModulePrefix _T("HistoryCache")
#define netflixModuleName                           _T("Netflix")
#define netflixDataStream netflixModulePrefix dataStreamPostfix

#define listsOfBestsModulePrefix                              _T("listsOfBests-")
#define listsOfBestsHistoryCacheName listsOfBestsModulePrefix _T("HistoryCache")
#define listsOfBestsModuleName                           _T("Lists of Bests")

#define lyricsModulePrefix                          _T("lyrics-")
#define lyricsHistoryCacheName lyricsModulePrefix _T("HistoryCache")
#define lyricsModuleName                            _T("Lyrics")

#define dictModulePrefix                         _T("dict-")
#define dictDefStream          dictModulePrefix  _T("def")
#define dictHistoryCacheName   dictModulePrefix  _T("HistoryCache")
#define dictModuleName                          _T("Dictionary")

#define pediaModulePrefix                        _T("pedia-")
#define pediaHistoryCacheName pediaModulePrefix  _T("HistoryCache")
#define pediaModuleName                         _T("Encyclopedia")

#define quotesModulePrefix                         _T("quotes-")
#define quotesModuleName                           _T("Quotes")
#define quotesDataStream quotesModulePrefix dataStreamPostfix

#define ebookModulePrefix                           _T("ebooks-")
#define ebookModuleName                           _T("eBooks")
#define ebookHistoryCacheName               ebookModulePrefix _T("HistoryCache")
#define ebookWelcomeCacheName            ebookModulePrefix _T("WelcomeCache")

#define flightsModulePrefix                         _T("flights-")
#define flightsDataStream flightsModulePrefix dataStreamPostfix

#define eBayModulePrefix                         _T("eBay-")
#define eBayHistoryCacheName eBayModulePrefix    _T("HistoryCache")
#define eBayModuleName                           _T("eBay")

extern void moviesDataRead(MoriartyApplication& app);

extern void weatherDataRead(MoriartyApplication& app);

extern void epicuriousDataRead(MoriartyApplication& app);

extern void m411DataRead(MoriartyApplication& app);

extern void boxOfficeDataRead(MoriartyApplication& app);

extern void dreamsDataRead(MoriartyApplication& app);

extern void horoscopeDataRead(MoriartyApplication& app);

extern void jokesDataRead(MoriartyApplication& app);

extern void stocksDataRead(MoriartyApplication& app);

extern void currencyDataRead(MoriartyApplication& app);

extern void gasPricesDataRead(MoriartyApplication& app);

extern void netflixDataRead(MoriartyApplication& app);

extern void quotesDataRead(MoriartyApplication& app);

extern void flightsDataRead(MoriartyApplication& app);

#endif
