#ifndef INFOMAN_PEDIA_ARTICLE_HANDLER_HPP__
#define INFOMAN_PEDIA_ARTICLE_HANDLER_HPP__

#include <FieldPayloadProtocolConnection.hpp>
#include <Definition.hpp>
#include <DynStr.hpp>

class DefinitionParser;
class ByteFormatParser;

class PediaArticleHandler: public FieldPayloadProtocolConnection::PayloadHandler
{
    DefinitionParser* definitionParser_;
    ByteFormatParser* byteFormatParser_;
    ulong_t           totalLength_;
    ulong_t           parsePosition_;
    ulong_t           articleLength_;
    ulong_t           linkedArticlesLength_;
    ulong_t           linkingArticlesLength_;
    CDynStr           buffer_;
    status_t          parsePartsLength();
    status_t          parsePart(bool finish);

    enum {partsLengthHeaderLen_ = 12};

public:

    const char_t*     defaultLanguage;

    DefinitionModel*  article;
    DefinitionModel*  linkedArticles;
    DefinitionModel*  linkingArticles;

    PediaArticleHandler();

    ~PediaArticleHandler();

    status_t handleIncrement(const char_t * payload, ulong_t& length, bool finish);

};

#endif // INFOMAN_PEDIA_ARTICLE_HANDLER_HPP__