#include "PediaArticleHandler.hpp"
#include "DefinitionParser.hpp"
#include <ByteFormatParser.hpp>
#include <LookupManager.hpp>

PediaArticleHandler::PediaArticleHandler():
    definitionParser_(NULL),
    byteFormatParser_(NULL),
    totalLength_(0),
    articleLength_(0),
    linkedArticlesLength_(0),
    linkingArticlesLength_(0),
    parsePosition_(0),
    defaultLanguage(NULL),
    article(NULL),
    linkedArticles(NULL),
    linkingArticles(NULL)
{
}

PediaArticleHandler::~PediaArticleHandler()
{
    delete definitionParser_;
    delete byteFormatParser_;
    
    delete article;
    delete linkingArticles;
    delete linkedArticles;
}

status_t PediaArticleHandler::handleIncrement(const char_t * payload, ulong_t& length, bool finish)
{
    if (0 == totalLength_)
    {
        definitionParser_ = new_nt DefinitionParser();
        if (NULL == definitionParser_)
            return memErrNotEnoughSpace;
            
        if (NULL != defaultLanguage)
            definitionParser_->defaultLanguage = defaultLanguage;
            
        byteFormatParser_ = new_nt ByteFormatParser();
        if (NULL == byteFormatParser_)
            return memErrNotEnoughSpace;
    }
    if (NULL == buffer_.AppendCharPBuf(payload, length))
        return memErrNotEnoughSpace;
    
    status_t err;
    if (totalLength_ < partsLengthHeaderLen_ && totalLength_ + length >= partsLengthHeaderLen_)
    {
        err = parsePartsLength();
        if (errNone != err)
            return err;
     }
    
    totalLength_ += length;
    if (totalLength_ < partsLengthHeaderLen_)
        return errNone;
    
    return parsePart(finish);
}

status_t PediaArticleHandler::parsePartsLength()
{
    const char* chr = buffer_.GetCStr();
    articleLength_ = readUnaligned32(chr);
    chr+= 4;
    linkedArticlesLength_ = readUnaligned32(chr);
    chr+= 4;
    linkingArticlesLength_ = readUnaligned32(chr);
    parsePosition_ = 12;
    DynStrRemoveStartLen(&buffer_, 0, partsLengthHeaderLen_);
    return errNone;
}

status_t PediaArticleHandler::parsePart(bool)
{
    ulong_t pos = parsePosition_ - partsLengthHeaderLen_;
    ulong_t len = totalLength_ - partsLengthHeaderLen_;
    ulong_t partLength = len;
    bool finish = false;
    status_t err;
    if (pos < articleLength_)
    {
        if (partLength >= articleLength_)
        {
            partLength = articleLength_ - pos;
            finish = true;
        }
        else
            partLength -= pos;
        err = definitionParser_->handleIncrement(buffer_.GetCStr(), partLength, finish);
        if (errNone != err)
            return err;

        if (finish)
        {
            article = definitionParser_->createModel();
            delete definitionParser_;
            if (NULL == article)
                return memErrNotEnoughSpace;
            definitionParser_ = NULL;
        }        
        finish = false;
        DynStrRemoveStartLen(&buffer_, 0, partLength);
        parsePosition_ += partLength;
        pos += partLength;
        partLength = len;
    }
    if (pos >= articleLength_ && pos < articleLength_ + linkedArticlesLength_)
    {
        partLength -= articleLength_;
        if (partLength >= linkedArticlesLength_)
        {
            partLength = (articleLength_ + linkedArticlesLength_) - pos;
            finish = true;
        }
        else 
            partLength -= (pos - articleLength_);
            
        err = byteFormatParser_->handleIncrement(buffer_.GetCStr(), partLength, finish);
        if (errNone != err)
            return err;
        
        if (finish)
        {   
            linkedArticles = byteFormatParser_->releaseModel();
            if (NULL == linkedArticles)
                return memErrNotEnoughSpace;
            byteFormatParser_->reset();
        }
        finish = false;
        DynStrRemoveStartLen(&buffer_, 0, partLength);
        parsePosition_ += partLength;
        pos += partLength;
        partLength = len;
    }
    if (pos >= articleLength_ + linkedArticlesLength_)
    {
        partLength -= (articleLength_ + linkedArticlesLength_);
        if (partLength > linkingArticlesLength_)
            return FieldPayloadProtocolConnection::errResponseMalformed;
        else if (partLength == linkingArticlesLength_)
        {
            partLength = (articleLength_ + linkedArticlesLength_ + linkingArticlesLength_) - pos;
            finish = true;
        }
        else
            partLength -= (pos - (articleLength_ + linkedArticlesLength_));
            
        err = byteFormatParser_->handleIncrement(buffer_.GetCStr(), partLength, finish);
        if (errNone != err)
            return err;
        
        if (finish)
        {   
            linkingArticles = byteFormatParser_->releaseModel();
            delete byteFormatParser_;
            if (NULL == linkingArticles)
                return memErrNotEnoughSpace;
            byteFormatParser_ = NULL;
        }
        DynStrRemoveStartLen(&buffer_, 0, partLength);
        parsePosition_ += partLength;
    }
    return errNone;
}