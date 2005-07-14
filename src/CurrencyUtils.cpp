#include "CurrencyUtils.h"
#include <Text.hpp>
#include <UniversalDataFormat.hpp>
#include <Currencies.hpp>

/*

template <class ForwardIterator, class T, class Compare>
ForwardIterator
lower_bound(ForwardIterator first, ForwardIterator last, const T& value, Compare comp)
{
    typedef typename iterator_traits<ForwardIterator>::difference_type difference_type;
    difference_type len = _STD::distance(first, last);
    while (len > 0)
    {
        ForwardIterator i = first;
        difference_type len2 = len / 2;
        _STD::advance(i, len2);
        if (comp(*i, value))
        {
            first = ++i;
            len -= len2 + 1;
        }
        else
            len = len2;
    }
    return first;
}

*/

int GetIndexOfCurrencyInUDF(const UniversalDataFormat& udf, const ArsLexis::char_t* symbol)
{
    uint_t first = 0;
    uint_t last = udf.getItemsCount();
    uint_t count = last;
    while (count > 0)
    {
        uint_t len = count / 2;
        uint_t i = first + len;
        if (0 > tstrcmp(udf.getItemText(i, currencySymbolIndex), symbol))
        {
            first = ++i;
            count -= len + 1;
        }
        else
            count = len;
    }
    if (udf.getItemsCount() == first)
        return -1;
    if (0 != tstrcmp(udf.getItemText(first, currencySymbolIndex), symbol))
        return -1;
    return first;
}

int GetIndexOfCurrencyInUDF(const UniversalDataFormat& udf, uint_t index)
{
    const char_t* symbol = getCurrencySymbol(index);
    return GetIndexOfCurrencyInUDF(udf, symbol);
}

double GetCurrencyRate(const UniversalDataFormat& udf, const ArsLexis::char_t* symbol)
{
    int i = GetIndexOfCurrencyInUDF(udf, symbol);
    if (-1 == i)
        return 0;

    const char_t* val = udf.getItemText(i, currencyRateIndex);
    double value;
    if (strToDouble(val, &value))
        return value;
    return 0;
}


double GetCurrencyRate(const UniversalDataFormat& udf, uint_t index)
{
    const char_t* symbol = getCurrencySymbol(index);
    return GetCurrencyRate(udf, symbol);
}

typedef char_t CurrencySymbol_t[4];
static const CurrencySymbol_t commonCurrencies[] = {"USD", "EUR", "JPY", "GBP"};

uint_t CommonCurrenciesCount()
{
    return ARRAY_SIZE(commonCurrencies);
}

const char_t* GetCommonCurrencySymbol(uint_t index)
{
    assert(index < ARRAY_SIZE(commonCurrencies));
    return commonCurrencies[index];
}

int GetCommonCurrencyIndex(const ArsLexis::char_t* symbol)
{
    for (uint_t i = 0; i < ARRAY_SIZE(commonCurrencies); ++i)
        if (0 == tstrcmp(symbol, commonCurrencies[i]))
            return i;
    return -1;
}

int GetCommonCurrencyIndex(uint_t index)
{
    return GetCommonCurrencyIndex(getCurrencySymbol(index));
}


bool IsCommonCurrency(const char_t* symbol)
{
   return -1 != GetCommonCurrencyIndex(symbol);
}

bool IsCommonCurrency(uint_t index)
{
    return -1 != GetCommonCurrencyIndex(index);
}

uint_t GetIndexOfCurrencyByFirstCharInUDF(const UniversalDataFormat& udf, char_t c)
{
    c = toUpper(c);
    uint_t first = 0;
    uint_t last = udf.getItemsCount();
    uint_t count = last;
    while (count > 0)
    {
        uint_t len = count / 2;
        uint_t i = first + len;
        if (udf.getItemText(i, currencySymbolIndex)[0] < c)
        {
            first = ++i;
            count -= len + 1;
        }
        else
            count = len;
    }
    if (udf.getItemsCount() == first)
        --first;
    return first;
}



