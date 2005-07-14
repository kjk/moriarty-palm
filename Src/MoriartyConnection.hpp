#ifndef __MORIARTY_CONNECTION_HPP__
#define __MORIARTY_CONNECTION_HPP__

#include "Text.hpp"

#include <FieldPayloadProtocolConnection.hpp>
#include <StringListPayloadHandler.hpp>
#include <HistoryCache.hpp>
#include "LookupManager.hpp"

class DataStoreWriter;

class MoriartyConnection: public FieldPayloadProtocolConnection {

    LookupManager& lookupManager_;
    uint_t         formatVersion_;

    LookupResult   result_;
    ServerError    serverError_;
    
    status_t prepareRequest();
    
    bool hasDisabledModules_;
    uint_t initialActiveModulesCount_;
    
    String moviesLocation_;

    bool getCurrenciesRequest_;

    String horoscopeSearchQuery_;

    String jokeUrl_;
    String jokesSearchQuery_;

    String stocksSymbols_;
    String stocksSymbolsValidateLast_;
    String stockUrl_;
    String stockName_;
    
    String weatherDisplayLocation_;
    String weatherInternalLocation_;
    
    String m411Zip_;
    String m411Area_;
    String m411City_;
    String m411State_;
    String m411FirstName_;
    String m411LastName_;
    String m411Phone_;
    int              m411InternationalCode_;
    String m411Name_;
    String m411Url_;
    bool m411SurroundingAreas_;
    bool m411NameSearch_;
    
    String tvProvidersZipCode_;
    char_t *url_;
    
    
    enum M411RequestType {
        requestNot411,
        requestGetReverseZip,
        requestGetReverseArea,
        requestGetZipByCity,
        requestGetAreaByCity,
        requestGetBusinessSearch,
        requestGetBusinessSearchByUrl,
        requestGetPersonSearch,
        requestGetReversePhone,
        requestGetInternational
    };

    M411RequestType m411RequestType_;
    
public:

    ulong_t        transactionId;
    
    ulong_t         flickrPictureCount;

    String         gasPricesZip;

    void setCurrenciesRequest() {getCurrenciesRequest_ = true;}

    void setHoroscope(const String& hor) {horoscopeSearchQuery_ = hor;}

    void setJoke(const String& url) {jokeUrl_ = url;}
    
    void setJokesList(const String& query) {jokesSearchQuery_ = query;}

    void setStocksList(const String& symbols) {stocksSymbols_ = symbols;}

    void setStocksListValidateLast(const String& symbols) {stocksSymbolsValidateLast_ = symbols;}

    void setStock(const String& url) {stockUrl_ = url;}

    void setStockByName(const String& url) {stockName_ = url;}

    void setWeatherLocation(const String& wl, const String& serverLoc) {weatherDisplayLocation_ = wl; weatherInternalLocation_ = serverLoc;}

    void setMoviesLocation(const char_t* loc) {moviesLocation_ = loc;}
    
    void set411ReverseZip(const String& zip);
    
    void set411ReverseArea(const String& area);

    void set411ZipByCity(const String& city, const String& state);

    void set411AreaByCity(const String& city, const String& state);
    
    void set411PersonSearch(const String& firstName, const String& lastName, const String& cityOrZip, const String& state);

    void set411BusinessSearch(const String& name, const String& cityOrZip, const String& state, bool surrounding, bool nameSearch);

    void set411BusinessSearchByUrl(const String& url);

    void set411ReversePhone(const String& phone);

    void set411InternationalCodeSearch(int countryCode);
    
    void setTvProvidersZipCode(const String& zipCode)  {tvProvidersZipCode_ = zipCode;}

    explicit MoriartyConnection(LookupManager& manager);
    
    ~MoriartyConnection();
    
    status_t enqueue();
    
    char_t *setUrl(const char_t *url);
    
protected:

    status_t handleField(const char_t *name, const char_t *value);
    
    void handleError(status_t error);
    
    status_t open();
    
    status_t notifyProgress();
    
    status_t notifyFinished();

    void setLookupResult(LookupResult res)
    {result_=res;}

    status_t notifyPayloadFinished();
    
    LookupManager& lookupManager()
    {return lookupManager_;}
    
    //enum {payloadFirstAvailable};
    
    status_t handlePayloadIncrement(const char_t * payload, ulong_t& length, bool finish);
    
private:

    typedef status_t (MoriartyConnection::* FieldHandler)(const String&, const String&);

    typedef status_t (MoriartyConnection::* PayloadCompletionHandler)(FieldPayloadProtocolConnection::PayloadHandler&);
    
    status_t handleCookieField(const String& name, const String& value);

    status_t handleDisabledModulesField(const String& name, const String& value);
    
    status_t handleFormatVersionField(const String& name, const String& value);

    status_t handleRegCodeDaysToExpire(const String& name, const String& value);

    status_t handleRegCodeValidField(const String& name, const String& value);

    status_t handleLatestClientVersionField(const String& name, const String& value);

    status_t handleTransactionIdField(const String& name, const String& value);

    status_t handleErrorField(const String& name, const String& value);
    
    status_t handleLocationAmbiguousField(const String& name, const String& value);
    
    status_t handlePediaLangsField(const String& name, const String& value);

    status_t handlePediaArticleField(const String& name, const String& value);
    
    status_t handlePediaArticleCountField(const String& name, const String& value);
    
    status_t handlePediaDbDateField(const String& name, const String& value);

    status_t handlePediaArticleTitleField(const String& name, const String& value);

    status_t handleStringListPayloadField(const String& name, const String& value);
    
    status_t handleByteFormatPayloadField(const String& name, const String& value);
    
    status_t handlePediaSearchField(const String& name, const String& value);
    
    status_t completePediaArticleField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    status_t completePediaSearchResultsField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completePediaLanguagesField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t handleEBookNameField(const String& name, const String& value);

    status_t handleEBookVersionField(const String& name, const String& value);
    
    status_t handleEBookDownloadField(const String& name, const String& value);
    
    status_t completeEBookBrowseField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    status_t completeEBookSearchResultsField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completeEBookDownloadField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    template<LookupResult result>
    status_t completeLocationAmbiguousField(FieldPayloadProtocolConnection::PayloadHandler& handler)
    {
        setLookupResult(result);
        StringListPayloadHandler& alh = static_cast<StringListPayloadHandler&>(handler);
        std::swap(lookupManager().locations, alh.strings);
        return errNone;
    }

    status_t completeMoviesDataField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completeWeatherDataField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completeGasPricesDataField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completeHoroscopesDataField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t completeCurrencyDataField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t complete411ReverseZipField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t complete411ReverseAreaField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    status_t complete411PersonSearchField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    status_t complete411BusinessSearchField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t complete411ReversePhoneField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    status_t complete411InternationalCodeField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t complete411AreaByCityField(FieldPayloadProtocolConnection::PayloadHandler& handler);

    status_t complete411ZipByCityField(FieldPayloadProtocolConnection::PayloadHandler& handler);
    
    struct FieldDescriptor {
    
        const char_t* name;
        
        enum FieldType {
            fieldValue,
            fieldPayloadUDF,
            fieldPayloadCustom
        } type;
        
        MoriartyConnection::FieldHandler fieldHandler;
        
        MoriartyConnection::PayloadCompletionHandler payloadCompletionHandler;
        
        UniversalDataFormat LookupManager::* destinationContainer;
        
        const char_t* sinkName;
        
        LookupResult lookupResult;
        
        bool sinkIsHistoryCache;
        
        bool operator<(const FieldDescriptor& desc) const {return 0 > tstrcmp(name, desc.name);}
        
        bool operator==(const FieldDescriptor& desc) const {return 0 == tstrcmp(name, desc.name);}
        
        bool operator!=(const FieldDescriptor& desc) const {return 0 != tstrcmp(name, desc.name);}
        
    };
    
    static const FieldDescriptor fields_[];
    
    const FieldDescriptor* currentField_;            
    
    HistoryCache cache_;
    DataStoreWriter* writer_;
    
    void prepareWriter();
    
private:
};

#endif


