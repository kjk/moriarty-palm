#include <Debug.hpp>

#include <SysUtils.hpp>

#include <TextElement.hpp>
#include <LineBreakElement.hpp>
#include <HorizontalLineElement.hpp>
#include <ParagraphElement.hpp>
#include <ListNumberElement.hpp>
#include <Text.hpp>
#include <Definition.hpp>
#include <BulletElement.hpp>

#include <StringListForm.hpp>

#include "TestWikiMainForm.hpp"
#include "MoriartyPreferences.hpp"

#include <ByteFormatParser.hpp>

#include <ExtendedEvent.hpp>

#include "HyperlinkHandler.hpp"
#include "LookupManager.hpp"

#include "MoriartyStyles.hpp"

TestWikiMainForm::TestWikiMainForm(MoriartyApplication& app):
    MoriartyForm(app, testWikiMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    nextButton_(*this),
    actTest_(0),
    testsCount_(0),
    txtRenderer_(*this, &scrollBar_)
{
    txtRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
    );  
    txtRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    setupPopupMenu(testWikiPopupMenu, MoriartyApplication::extEventShowMenu, app.hyperlinkHandler);

    setFocusControlId(testWikiRenderer);

}

TestWikiMainForm::~TestWikiMainForm() 
{
}

void TestWikiMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneButton_.attach(doneButton);
    nextButton_.attach(nextButton);
    txtRenderer_.attach(testWikiRenderer);
    txtRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
}

int TestWikiMainForm::showStringListForm(char_t* strList[], int strListSize)
{
    StringListForm* form = new StringListForm(application(), stringListForm, stringList, selectButton, cancelButton);
    form->initialize();
    form->SetStringList(application().strListSize, application().strList);
    // ignoreEvents_ = true; // Strange things happen here and if we don't prevent MainForm from processing events we'll overflow the stack :-(
    int sel = form->showModalAndGetSelection();
    //ignoreEvents_ = false;
    update();
    delete form;
    return sel;    
}

#define TEXT_DB_CREATOR 'wIKi'
#define TEXT_DB_TYPE    'TesT'

bool TestWikiMainForm::handleOpen()
{
    MemHandle   recHandle = NULL;
    char_t *    recData = NULL;
    bool handled = MoriartyForm::handleOpen();

    DmOpenRef dbRef = DmOpenDatabaseByTypeCreator(TEXT_DB_TYPE, TEXT_DB_CREATOR, dmModeReadOnly );
    if (NULL == dbRef)
    {
        FrmAlert(alertNoTextDatabase);
        application().runMainForm();
        return true;
    }

    recHandle = DmGetRecord(dbRef, 0);
    recData = (char_t*)MemHandleLock(recHandle);

    String txt(recData);
    
    FreeStringList(application().strList, application().strListSize);
    
    application().strList = StringListFromString(txt, "##", application().strListSize);
    
    testsCount_ = application().strListSize;

    sendEvent(MoriartyApplication::appSelectText);

Exit:
    if (NULL != recData)
    {
        MemPtrUnlock(recData);
        DmReleaseRecord(dbRef, 0, true);
    }

    if (NULL != dbRef)
        DmCloseDatabase(dbRef);

    return handled;
}

class TextToDefinitionParser
{
    private:
        enum TagCode{
            tagCodeBr,
            tagCodeB,
            tagCodeJustify,
            tagCodeA,
            tagCodeBull,
            tagCodeHr,
            tagCodeP,
            tagCodeLi,
            
            //TODO:...
            
            
                    
            tagCodeUnknown
        };
    
        struct TagStructure
        {
            TagCode nameCode;
            String  args;
            DefinitionElement* tagElement;
            
            ~TagStructure()
            {
                args.clear();
            }
            
            TagStructure()
            {
                nameCode = tagCodeUnknown;
                args.clear();
                tagElement = NULL;            
            }
        };
    
        typedef std::list<TagStructure*> Tags_t;
        Tags_t   tags_;

        String              inText_;
        ulong_t             inLength_;
        String::size_type   start_;
        bool                finish_;

        ArsLexis::status_t parse();        

        TagCode getTagCodeFromName(const char_t* name, ulong_t len);

        String::size_type skipDoubleChar(String::size_type startPos, const char_t ch);

        String::size_type findEndOfTag(String::size_type next);
        
        void performStartTagAction(bool selfClosing);
        
        void formatLastElement();
        
        void doEscaping(String& str);
        
    public:

        Definition::Elements_t  elems_;

        TextToDefinitionParser();

        ~TextToDefinitionParser();

        void reset();
       
        ArsLexis::status_t handleIncrement(const char_t* text, ulong_t length, bool finish=false);
        
        void getElements(Definition::Elements_t& el)
        {
            el.swap(elems_);
        }
};

TextToDefinitionParser::TextToDefinitionParser():
    inLength_(0),
    start_(0),
    finish_(false)
{
    inText_.clear();
    tags_.clear();
}

void TextToDefinitionParser::reset()
{
    std::for_each(tags_.begin(), tags_.end(), ObjectDeleter<TagStructure>());
    tags_.clear();
    DestroyElements(elems_);
    start_ = 0;
    inLength_ = 0;
    finish_ = false;
    inText_.clear();
}

TextToDefinitionParser::~TextToDefinitionParser()
{
    std::for_each(tags_.begin(), tags_.end(), ObjectDeleter<TagStructure>());
    tags_.clear();
    DestroyElements(elems_);
}

TextToDefinitionParser::TagCode TextToDefinitionParser::getTagCodeFromName(const char_t* name, ulong_t len)
{
    if (len > 0)
    {
        switch(toLower(name[0]))
        {
            case _T('b'):
                if (len == 1)
                    return tagCodeB;
                else
                {
                    if (len == 2 && toLower(name[1]) == _T('r'))
                        return tagCodeBr;
                    if (len == 4)
                        if (toLower(name[1]) == _T('u') && toLower(name[2]) == _T('l') && toLower(name[3]) == _T('l'))
                            return tagCodeBull;
                }
                break;
            case _T('a'):
                if (len == 1)
                    return tagCodeA;
                break;
            case _T('p'):
                if (len == 1)
                    return tagCodeP;
                break;
            case _T('h'):
                if (len == 2)
                    if (toLower(name[1]) == _T('r'))
                        return tagCodeHr;
            case _T('l'):
                if (len == 2)
                    if (toLower(name[1]) == _T('i'))
                        return tagCodeLi;
            case _T('j'):
                //bad
                if (len == 7)
                    if (toLower(name[1]) == _T('u') &&
                        toLower(name[2]) == _T('s') &&                    
                        toLower(name[3]) == _T('t') &&                    
                        toLower(name[4]) == _T('i') &&                    
                        toLower(name[5]) == _T('f') &&                    
                        toLower(name[6]) == _T('y')                   
                    )
                    return tagCodeJustify;
                
                break;
            
        }   
    }
       
    return tagCodeUnknown;
}

/**
 parse next portion of data (if tag is not closed - keep it in memory)
 */
ArsLexis::status_t TextToDefinitionParser::handleIncrement(const char_t* inputText, ulong_t inputLength, bool finish)
{
    inText_.append(inputText,0,inputLength);
    inLength_ += inputLength;
    start_ = 0;
    finish_ = finish;
    
    if (inLength_ == 0)
        return errNone;
    status_t error = parse();
    return error;
}

/**
 used to ignore << and >> when searching for "<tag..." and "...ag>"
 */
String::size_type TextToDefinitionParser::skipDoubleChar(String::size_type startPos, const char_t ch)
{
    if (startPos >= inLength_)
        return startPos;
    assert(ch == inText_[startPos]);
    bool escaping = true;
    while (escaping)
    {
        escaping = false;
        if (startPos < inLength_ - 1)
            if (ch == inText_[startPos+1])
            {
                startPos = inText_.find(ch, startPos+2);
                escaping = true;
            }    
    }
    return startPos;
}

/**
 replace '<<' with '<' and '>>' with '>' in text
 clear mess with '\n' (remove them)
 */
void TextToDefinitionParser::doEscaping(String& str)
{
    String::size_type pos = 0;
    while (pos < str.length())
    {
        switch(str[pos])
        {
            case _T('<'):
                if (pos + 1 < str.length())
                    if (str[pos+1] == _T('<'))
                        str.erase(pos,1);
                pos++;
                break;

            case _T('>'):
                if (pos + 1 < str.length())
                    if (str[pos+1] == _T('>'))
                        str.erase(pos,1);
                pos++;
                break;
                
            case _T('\n'):
                str.erase(pos,1);
                break;

            case _T(13):
                str.erase(pos,1);
                break;

            default:
                pos++;
                break;        
        }   
    }
}

/**
  if selfClosing - pop tag from vector
 */
void TextToDefinitionParser::performStartTagAction(bool selfClosing)
{
    bool addingElement = true;
    switch(tags_.back()->nameCode)
    {
        case tagCodeBr:
            elems_.push_back((tags_.back()->tagElement = new LineBreakElement()));
            selfClosing = true;
            break;

        case tagCodeHr:
            elems_.push_back((tags_.back()->tagElement = new HorizontalLineElement()));
            selfClosing = true;
            break;

        case tagCodeBull:
            elems_.push_back((tags_.back()->tagElement = new BulletElement()));
            break;

        case tagCodeP:
            elems_.push_back((tags_.back()->tagElement = new ParagraphElement()));
            break;

        case tagCodeLi:
            long number = 0;
            status_t error = numericValue(tags_.back()->args, number);
            assert(error == errNone);
            assert(number >= 0 && number < 1000);
            elems_.push_back((tags_.back()->tagElement = new ListNumberElement((uint_t) number)));
            break;

        //TODO: add more



        // tags with no action (no break;)
        case tagCodeB: 
        case tagCodeA:
        case tagCodeJustify:
            addingElement = false;
            break;

        case tagCodeUnknown:
            //assert(false);
            addingElement = false;
            break;
            
        default:
            assert(false);
            addingElement = false;
            break;
    }

    // if <.../>
    if (selfClosing)
    {
        delete tags_.back();
        tags_.pop_back();    
    }

    // if adding element
    if (addingElement)
        formatLastElement();
}

/**
 format last element using informations from tagVec
 */
void TextToDefinitionParser::formatLastElement()
{
    //TODO: add formatting
    
    
    DefinitionElement* el = elems_.back();
    el->setParent(NULL);
    
    Tags_t::iterator end = tags_.end();
    for (Tags_t::iterator it = tags_.begin(); it != end; ++it) 
    {
        switch((*it)->nameCode)
        {
            //TODO: add more

            case tagCodeB:
                el->setStyle(StyleGetStaticStyle(styleNameBold));
                break;

            case tagCodeJustify:
                if (!((*it)->args.empty()))
                {
                    //TODO: change it to strcmp ?
                    switch(toLower((*it)->args[0]))
                    {
                        case _T('l'):
                            el->setJustification(DefinitionElement::justifyLeft);
                            break;
                        case _T('c'):
                            el->setJustification(DefinitionElement::justifyCenter);
                            break;
                        case _T('r'):
                            //right, or right last element?
                            if ((*it)->args.length() == 5 || (*it)->args.length() == 1)
                                el->setJustification(DefinitionElement::justifyRight);
                            else
                                el->setJustification(DefinitionElement::justifyRightLastElementInLine);
                            break;
                        default:
                            assert(false);
                            break;
                    }
                
                }
                break;

            case tagCodeA:
                el->setHyperlink((*it)->args, hyperlinkUrl);
                break;

            case tagCodeBull: //no break
            case tagCodeP: //no break
            case tagCodeLi:
                if (el != (*it)->tagElement)
                    el->setParent((*it)->tagElement);
                break;

            // tags with no rules apply
            case tagCodeUnknown:
                //assert(false);
                break;
            default:
                assert(false);
                break;
        }                        
    }              
}

/**
  tags can include other tags... so this is not so easy
  return:
    * index of '>'
    * next if '>' not found and !finish_ 
    * npos if '>' not found and finish_
 */
String::size_type TextToDefinitionParser::findEndOfTag(String::size_type next)
{
    int unclosed = 0;
    String::size_type pos = next+1;
    String::size_type lastStart = pos;
    String::size_type lastEnd = pos;
                
    bool foundLastEnd = false;
    while (!foundLastEnd)
    {
        lastStart = inText_.find(_T('<'), lastStart);
        lastEnd = inText_.find(_T('>'), lastEnd);
        // escaping for both
        lastEnd = skipDoubleChar(lastEnd,_T('>'));
        lastStart = skipDoubleChar(lastStart,_T('<'));
        // finaly found lastEnd?
        if (unclosed <= 0 && lastEnd <= lastStart)
            foundLastEnd = true;
        else
        {
            if (lastStart < lastEnd)
            {
                lastStart++;
                unclosed++;
            }
            else if(lastStart > lastEnd)
            {
                lastEnd++;
                unclosed--;
            }
            else
            {
                // both are > inLength_
                if (finish_)
                    assert(unclosed <= 0);                
                unclosed = 0;
            }
        }                
    }
    if (lastEnd < inLength_)
        return lastEnd;
    else
        if (finish_)
            return lastEnd;
        else
            return next;
}

/**
 parsing!

 */
ArsLexis::status_t TextToDefinitionParser::parse()
{
    TextElement* textElement;
    using namespace std;

    String::size_type next = start_;
    String            str;
    while (true) 
    {
        next = inText_.find(_T('<'), start_);
        // skipping <<
        next = skipDoubleChar(next,_T('<'));
        
        if (next > start_)
        {
            if (next > inLength_)
                str.assign(inText_, start_, next);
            else
                str.assign(inText_, start_, next-start_);
            doEscaping(str);
            if (!str.empty())
            {
                elems_.push_back(textElement = new TextElement(str));
                formatLastElement();
            }
        }
        // exit if EOT
        if (next > inLength_)
        {
            //this is end of text (so far), so remove it from memory
            inLength_ = 0;
            inText_.clear();
            start_ = 0;        
            return errNone;
        }
        // detect what was found after <
        start_ = next;
        next = findEndOfTag(next);
        if (next == start_)
        {
            // not found, but text is not finished!
            assert(!finish_);
            inText_.erase(0,next);
            inLength_ -= next;
            start_ = 0;
            return errNone;                
        }
        else if (next >= inLength_)
        {
            // do nothing... this looks like corrupted data?
            start_ = start_+1; //to skip '<'
        }
        else
        {
            if (inText_[start_+1] == _T('/'))
            {
                // closing tag
                str.assign(inText_, start_+2, next-start_-2);
                if (tags_.size() > 0)
                {
                
                    TagCode tc = getTagCodeFromName(&str[0], str.length());
                    bool foundEqualStartTag = false;

                    Tags_t::iterator founded = tags_.end();
                    Tags_t::iterator end = founded;
                    for (Tags_t::iterator it = tags_.begin(); it != end; ++it) 
                    {
                        if ((*it)->nameCode == tc)
                        {
                            founded = it;
                        }                        
                    }              
                    if (founded != end)
                    {
                        delete (*founded);
                        tags_.erase(founded);
                        foundEqualStartTag = true;
                    }
                    if (!foundEqualStartTag)
                        assert(false);
                }
                else
                    assert(false);
            }
            else
            {
                // start tag
                bool selfClosing = false;
                if (inText_[next-1] == _T('/'))
                {
                    selfClosing = true;
                    str.assign(inText_, start_+1, next-start_-2);
                }
                else    
                    str.assign(inText_, start_+1, next-start_-1);
                //add it to vector... (as name, args)
                String::size_type pos = str.find(_T(' '), 0);
                if (pos >= str.length())
                    pos = str.length();
                TagStructure* ts = new TagStructure();
                ts->nameCode = getTagCodeFromName(&str[0],pos);
                if (pos < str.length())
                    ts->args.assign(str,pos+1,str.npos);
                tags_.push_back(ts);
                performStartTagAction(selfClosing);
            }
            start_ = next + 1;       
        }
    }

    return errNone;
}

// TODO: this needs to be a real parser
void TestWikiMainForm::parseText(int recNo)
{
    MemHandle   recHandle = NULL;
    char *    recData;
    UInt32      recSize;
    ulong_t length;

    DmOpenRef dbRef = DmOpenDatabaseByTypeCreator(TEXT_DB_TYPE, TEXT_DB_CREATOR, dmModeReadOnly );
    if (NULL == dbRef)
    {
        FrmAlert(alertNoTextDatabase);
        application().runMainForm();
    }

    recHandle = DmGetRecord(dbRef, recNo);
    assert(NULL != recHandle);
    if (NULL == recHandle)
        return;

    recData = (char_t*)MemHandleLock(recHandle);
    recSize = MemHandleSize(recHandle);

    assert(recSize >= 1);
    if (recSize<1)
        return;

    DefinitionModel* model = NULL;
    if ('?' == recData[0])
    {
        ByteFormatParser parser;
        assert(recSize>=5);
        if (recSize < 5)
            return;
        length = readUnaligned32(&recData[1]);
        parser.handleIncrement(&recData[5], length, true);
        model = parser.releaseModel();
        if (NULL != model->title())
        {
            title_ = model->title();
            setTitle(model->title());
        }    
    }
    else
    {
        ByteFormatParser parser;
        assert(recSize>=4);
        if (recSize < 4)
            return;
        parser.parseAll(&recData[0], (UInt32)(-1));
        model = parser.releaseModel();
        if (NULL != model->title())
        {
            title_ = model->title();
            setTitle(model->title());
        }    
    }
    // end of parser

    if (NULL != recData)
    {
        MemPtrUnlock(recData);
        DmReleaseRecord(dbRef, recNo, true);
    }

    if (NULL != dbRef)
        DmCloseDatabase(dbRef);

    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    txtRenderer_.setModel(model, Definition::ownModel);
    update();
}

void TestWikiMainForm::selectText()
{
    int sel = showStringListForm(application().strList, application().strListSize);

    //FreeStringList(application().strList, application().strListSize);
    if (NOT_SELECTED == sel)
        return;

    actTest_ = sel+1;
    parseText(sel+1);
    
}

void TestWikiMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds==bounds)
        return;
    setBounds(bounds=screenBounds);

    txtRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    nextButton_.anchor(screenBounds, anchorLeftEdge, 34, anchorTopEdge, 14);
    update();    
}

bool TestWikiMainForm::handleEvent(EventType& event)
{
    if (txtRenderer_.handleEventInForm(event))
        return true;

    bool handled = false;
    
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
            
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case MoriartyApplication::appSelectText:
            selectText();
            handled = true;
            break;
            
        case LookupManager::lookupFinishedEvent:
            return HandleCrossModuleLookup(event, NULL, NULL);
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

void TestWikiMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;

        case nextButton:
            handleNextButton();
            update();
            break;

        default:
            assert(false);
    }
}

void TestWikiMainForm::handleNextButton()
{
    actTest_++;
    if (actTest_ > testsCount_)
        actTest_ = 1;
    if (testsCount_ > 0)
        parseText(actTest_);
}

bool TestWikiMainForm::handleKeyPress(const EventType& event)
{
    bool handled = false;
    int option = List::optionScrollPagesWithLeftRight;
    if (application().runningOnTreo600())
        option = 0;

    return handled;
}
