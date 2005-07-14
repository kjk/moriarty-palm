#include "ModulesData.hpp"
#include <DataStore.hpp>
#include "LookupManager.hpp"
#include <UniversalDataHandler.hpp>

void moviesDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(moviesDataStream, lm->moviesData);   
}

void weatherDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(weatherDataStream, lm->weatherData);   
}

void epicuriousDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(epicuriousRecipesListStream, lm->recipeMetrics);
    readUniversalDataFromStream(epicuriousRecipeStream, lm->recipe);
}

void m411DataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(m411PersonDataStream, lm->personList);
    readUniversalDataFromStream(m411BusinessDataStream, lm->businessList);
}

void boxOfficeDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(boxOfficeDataStream, lm->boxOfficeData);   
}

void dreamsDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(dreamsDataStream, lm->dream);   
}

void jokesDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(jokesJokesListStream, lm->jokes);
    readUniversalDataFromStream(jokesJokeStream, lm->joke);
}

void currencyDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(currencyDataStream, lm->currencyData);   
}

void stocksDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(stocksStocksListStream, lm->stocks);
}

void gasPricesDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(gasPricesStream, lm->gasPrices);
}

void horoscopeDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(horoscopeDataStream, lm->horoscope);
}

void netflixDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(netflixDataStream, lm->netflixQueue);
}

void quotesDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(quotesDataStream, lm->quotesData);
}

void flightsDataRead(MoriartyApplication& app)
{
    LookupManager* lm=app.lookupManager;
    assert(NULL != lm);
    readUniversalDataFromStream(flightsDataStream, lm->flightsData);
}
