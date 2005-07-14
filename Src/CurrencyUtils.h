#ifndef CURRENCY_UTILS_H__
#define CURRENCY_UTILS_H__

#include <Debug.hpp>
#include <BaseTypes.hpp>
#include <vector>

enum CurrencyIndexInUDF {
    currencySymbolIndex,
    currencyRateIndex
};

class UniversalDataFormat;

typedef std::vector<uint_t> SelectedCurrencies_t;

int GetIndexOfCurrencyInUDF(const UniversalDataFormat& udf, uint_t index);

int GetIndexOfCurrencyInUDF(const UniversalDataFormat& udf, const ArsLexis::char_t* symbol);

double GetCurrencyRate(const UniversalDataFormat& udf, uint_t index);

double GetCurrencyRate(const UniversalDataFormat& udf, const ArsLexis::char_t* symbol);

uint_t CommonCurrenciesCount();

const ArsLexis::char_t* GetCommonCurrencySymbol(uint_t index);

bool IsCommonCurrency(uint_t index);

bool IsCommonCurrency(const ArsLexis::char_t* symbol);

int GetCommonCurrencyIndex(uint_t index);

int GetCommonCurrencyIndex(const ArsLexis::char_t* symbol);

uint_t GetIndexOfCurrencyByFirstCharInUDF(const UniversalDataFormat& udf, ArsLexis::char_t c);

#endif