#include "M411MainForm.hpp"
#include "LookupManager.hpp"
#include <SysUtils.hpp>
#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakELement.hpp>
#include <HorizontalLineElement.hpp>
#include <BulletElement.hpp>
#include <algorithm>
#include <Text.hpp>
#include <MemoPad.hpp>
#include <AddressBook.hpp>
#include <UniversalDataHandler.hpp>
#include <PhoneCall.hpp>

#if defined(__MWERKS__)
# pragma far_code
#endif

/***
    DONE:
    8 of 8
    TODO:

    - address book and memo - category (Unfiled for now)
    
    IMPORTANT:
    - 411 works with events - some popups need to recive 
        proper event after opened
        because many popups are shared. (EnterCityForm - zip or area)
    - ResultsListDrawHandler have its own display modes - they are
        also item heights. There is no method to get mode back, so
        you need to use .itemHeight() method.
    - informations area store in shared UDFs:
        (areaCode, zipCode, reverseAreaCode, reverseZipCode)
        (personSearch, reversePhone)
        (businessSearch)
        (internationalCallingCode)
    - personSearch and businessSearch are stored
    
*/

// indexes in UDF
#define nameIndexInUDF          0
#define addressIndexInUDF       1
#define cityIndexInUDF          2
#define phoneIndexInUDF         3
#define zipAreaCityIndexInUDF   0
#define countryIndexInUDF       1
#define timeZoneIndexInUDF      2
#define countryCodeIndexInUDF   0
#define cityNameIndexInUDF      0
#define cityCodeIndexInUDF      1

class SearchListDrawHandler: public BasicStringItemRenderer {
    
    const uint_t modulesCount_;
    const M411MainForm::m411ModuleDef_t *moduleDefs_;
        
public:
    
    SearchListDrawHandler(const int modulesCount, const M411MainForm::m411ModuleDef_t *moduleDefs) :
        modulesCount_(modulesCount), moduleDefs_(moduleDefs)
    {}

    uint_t itemsCount() const
    {return modulesCount_;}

    ~SearchListDrawHandler();
    
protected:

    void getItem(String& out, uint_t item)
    {
        out.assign(moduleDefs_[item].name_);
    }
};

SearchListDrawHandler::~SearchListDrawHandler()
{}

class ResultsListDrawHandler: public ExtendedList::ItemRenderer {

    UniversalDataFormat* results_;

public:

    enum ResultsMode
    {
        zipAreaCityMode = 12, //this is itemHeight too !!!
        personMode = 50,
        businessMode = 49,
        internationalMode = 14
    };

private:
    
    ResultsMode resultsMode_;
    
public:

    ResultsListDrawHandler(UniversalDataFormat* res, ResultsMode mode):
        results_(res), resultsMode_(mode) {}
        
    uint_t itemsCount() const
    { 
        return results_->getItemsCount();
    }

    ~ResultsListDrawHandler();

    void drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    void drawItemZipAreaCity(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    void drawItemPerson(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);

    void drawItemCountry(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds);
    
protected:

/*
    void getItem(String& out, uint_t item)
    {
        out.assign(results_->getItemText(item,0)); //0 - first item information 
    }
*/    
};

ResultsListDrawHandler::~ResultsListDrawHandler()
{}

void ResultsListDrawHandler::drawItemZipAreaCity(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    Point newTop = itemBounds.topLeft;
    //set display offsets:
    uint_t display1 = itemBounds.width();
    uint_t display2 = itemBounds.width();

    uint_t display3 = itemBounds.width();

    uint_t width=display1;
    String text;
    text.assign(results_->getItemText(item,zipAreaCityIndexInUDF));
    uint_t length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

    width=display2;
    text.assign(results_->getItemText(item,countryIndexInUDF));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    newTop.x = itemBounds.width()-width;
    graphics.drawText(text.c_str(), length, newTop);

    if (itemBounds.height()/2 <= 14)
        return;

    newTop = itemBounds.topLeft;
    newTop.y += itemBounds.height()/2;
    width=display3;
    text.assign(results_->getItemText(item,timeZoneIndexInUDF));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);
}

void ResultsListDrawHandler::drawItemCountry(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    Point newTop = itemBounds.topLeft;
    uint_t width=itemBounds.width();
    String text;
    if (1 == results_->getItemElementsCount(item))
    {
        text.assign(results_->getItemText(item,countryCodeIndexInUDF));
        uint_t length=text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        graphics.drawText(text.c_str(), length, newTop);
    }
    else
    {
        text.assign(results_->getItemText(item,cityNameIndexInUDF));
        uint_t length=text.length();
        graphics.charsInWidth(text.c_str(), length, width);
        graphics.drawText(text.c_str(), length, newTop);
        
        text.assign(results_->getItemText(item,cityCodeIndexInUDF));
        length=text.length();
        width=itemBounds.width();
        graphics.charsInWidth(text.c_str(), length, width);
        newTop.x = itemBounds.width()-width-2; //-2 just to be nice
        graphics.drawText(text.c_str(), length, newTop);
    }
}

void ResultsListDrawHandler::drawItemPerson(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    Point newTop = itemBounds.topLeft;
    uint_t displayDY = itemBounds.height()/4;

    uint_t width=itemBounds.width();
    String text;
    text.assign(results_->getItemText(item,nameIndexInUDF));
    uint_t length=text.length();
    graphics.stripToWidthWithEllipsis(text, length, width);
    graphics.drawText(text.c_str(), length, newTop);

    newTop.y += displayDY;
    width=itemBounds.width();
    text.assign(results_->getItemText(item,addressIndexInUDF));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

    newTop.y += displayDY;
    width=itemBounds.width();
    text.assign(results_->getItemText(item,cityIndexInUDF));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

    newTop.y += displayDY;
    width=itemBounds.width();
    text.assign(results_->getItemText(item,phoneIndexInUDF));
    length=text.length();
    graphics.charsInWidth(text.c_str(), length, width);
    graphics.drawText(text.c_str(), length, newTop);

}

void ResultsListDrawHandler::drawItem(Graphics& graphics, ExtendedList& list, uint_t item, const ArsRectangle& itemBounds)
{
    switch(resultsMode_)
    {
        case zipAreaCityMode:
            drawItemZipAreaCity(graphics,list,item,itemBounds);
            break;
        case personMode: //no break
        case businessMode:
            drawItemPerson(graphics,list,item,itemBounds);
            break;
        case internationalMode:
            drawItemCountry(graphics,list,item,itemBounds);
            break;
        default:
            assert(false);
            break;
    }
}

#define DEF_S_ITEM(NAME,FORM_ID) \
   { NAME ## Txt, FORM_ID, M411MainForm::dm_ ## NAME, NAME ## MenuItem },

M411MainForm::m411ModuleDef_t M411MainForm::moduleDefs_[M411_MODULES_COUNT] =
{
    DEF_S_ITEM(personSearch, m411EnterPersonForm)
    DEF_S_ITEM(businessSearch, m411EnterBusinessForm)
    DEF_S_ITEM(reversePhone, m411EnterPhoneForm)
    DEF_S_ITEM(zipCode, m411EnterCityForm)
    DEF_S_ITEM(reverseZipCode, m411EnterZipForm )
    DEF_S_ITEM(areaCode, m411EnterCityForm )
    DEF_S_ITEM(reverseAreaCode, m411EnterAreaForm )
    DEF_S_ITEM(internationalCodes, selectStateForm )
};  

M411MainForm::~M411MainForm()
{
}

M411MainForm::M411MainForm(MoriartyApplication& app):
    MoriartyForm(app, m411MainForm),
    displayMode_(showSearch),
    displayModeToSetAfterLookup_(showSearch),
    resultsList_(*this),
    searchList_(*this),
    searchButton_(*this),
    backButton_(*this),
    doneButton_(*this)
{}

void M411MainForm::attachControls()
{
    MoriartyForm::attachControls();
    searchList_.attach(searchList);
    searchList_.setItemHeight(14);
    searchList_.setUpBitmapId(upBitmap);
    searchList_.setDownBitmapId(downBitmap);

    resultsList_.attach(resultsList);
    resultsList_.setItemHeight(16);
    resultsList_.setUpBitmapId(upBitmap);
    resultsList_.setDownBitmapId(downBitmap);

    searchButton_.attach(searchButton);
    doneButton_.attach(doneButton);
    backButton_.attach(backButton);
}

bool M411MainForm::handleOpen()
{
    bool res=MoriartyForm::handleOpen();
    
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL != lookupManager);
    universalDataZipAreaCity_ = &lookupManager->universalDataZipAreaCity;
    personList_ = &lookupManager->personList;
    businessList_ = &lookupManager->businessList;
    internationalList_ = &lookupManager->internationalList;

    searchList_.setCustomDrawHandler(searchListDrawHandler_.get());
    searchListDrawHandler_.reset(new SearchListDrawHandler(M411_MODULES_COUNT, (const M411MainForm::m411ModuleDef_t *)&moduleDefs_));
    searchList_.setCustomDrawHandler(searchListDrawHandler_.get());
    searchList_.setSelection(0);

    resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
    
    setDisplayMode(displayMode_);
    update();
    return res;
}

void M411MainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
        
    setBounds(screenBounds);
    
    resultsList_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 36);
    resultsList_.adjustVisibleItems();    

    searchList_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 36);
    searchList_.adjustVisibleItems();

    static const uint_t buttonsTopEdge = 14;
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, buttonsTopEdge);
    backButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, buttonsTopEdge);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 42, anchorTopEdge, buttonsTopEdge);
    update();    
}

void M411MainForm::handleControlSelect(const EventType& event)
{
    MoriartyApplication& app=application();
    switch (event.data.ctlSelect.controlID)
    {
        case searchButton:
            uint_t currentSearch = -1;
            for (uint_t i = 0; i < M411_MODULES_COUNT; i++)
                if (moduleDefs_[i].displayMode_ == displayMode_)
                    currentSearch = i;
            if (-1 != currentSearch)
                handleSearchItemSelected(currentSearch);                
            else
                setDisplayMode(showSearch);
            break;
            
        case doneButton:
            application().runMainForm();
            break;            
            
        case backButton:
            setDisplayMode(showSearch);
            update();
            break;            
 
        default:
            assert(false);
    }
}

inline void M411MainForm::setControlsState(bool enabled)
{
    searchButton_.setEnabled(enabled);
}

void M411MainForm::updateTitle(void)
{    
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);

    const char_t* title = NULL;

    switch(displayMode_)
    {
        case showSearch:
            title = _T("411");
            break;

        case dm_reverseZipCode:
        case dm_reverseAreaCode:
        case dm_areaCode:
        case dm_zipCode:
            title = lookupManager->getLast411SearchAreaCityZip();
            break;

        case dm_personSearch:
            title = lookupManager->getLast411Search(LookupManager::personSearchTitle);
            break;

        case dm_reversePhone:
            title = lookupManager->getLast411Search(LookupManager::reversePhoneTitle);
            break;
            
        case dm_internationalCodes:
            title = lookupManager->getLast411Search(LookupManager::internationalCallingCodeTitle);
            break;
            
        case dm_businessSearch:
            title = lookupManager->getLast411Search(LookupManager::businessSearchTitle);
            break;
    }
    if (NULL == title)
        setTitle(_T("Last search results"));
    else if (tstrlen(title) == 0)
        setTitle(_T("Last search results"));
    else
        setTitle(title);

    update();
}

void M411MainForm::updateAfterLookup(LookupManager& lookupManager)
{
    universalDataZipAreaCity_ = &lookupManager.universalDataZipAreaCity;
    setDisplayMode(displayModeToSetAfterLookup_);
    resultsList_.notifyItemsChanged();
    if (0 != resultsList_.itemsCount())
        resultsList_.setSelection(0, ExtendedList::redrawNot);
    update();    
}

void M411MainForm::updateAfterLookupPersonSearch(LookupManager& lookupManager)
{
    personList_ = &lookupManager.personList;
    setDisplayMode(displayModeToSetAfterLookup_);
    resultsList_.notifyItemsChanged();
    if (0 != resultsList_.itemsCount())
        resultsList_.setSelection(0, ExtendedList::redrawNot);
    update();    
}

void M411MainForm::updateAfterLookupBusinessSearch(LookupManager& lookupManager)
{
    businessList_ = &lookupManager.businessList;
    setDisplayMode(displayModeToSetAfterLookup_);
    resultsList_.notifyItemsChanged();
    if (0 != resultsList_.itemsCount())
        resultsList_.setSelection(0, ExtendedList::redrawNot);
    update();    
}

void M411MainForm::updateAfterLookupInternational(LookupManager& lookupManager)
{
    internationalList_ = &lookupManager.internationalList;
    setDisplayMode(displayModeToSetAfterLookup_);
    resultsList_.notifyItemsChanged();
    if (0 != resultsList_.itemsCount())
        resultsList_.setSelection(0, ExtendedList::redrawNot);
    update();    
}

void M411MainForm::handleLookupFinished(const EventType& event)
{
    setControlsState(true);
    
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResult411ReverseZip: //no break
        case lookupResult411ReverseArea: //no break
        case lookupResult411AreaByCity: //no break
        case lookupResult411ZipByCity: 
            updateAfterLookup(*lookupManager);
            break;

        case lookupResult411AreaByCityMultiselect: 
            Application::popupForm(selectLocationForm);
            sendEvent(MoriartyApplication::app411SetAreaByCityEvent);
            break;

        case lookupResult411ZipByCityMultiselect:
            Application::popupForm(selectLocationForm);
            sendEvent(MoriartyApplication::app411SetZipByCityEvent);
            break;

        case lookupResult411PersonSearchCityMultiselect:
            Application::popupForm(selectLocationForm);
            sendEvent(MoriartyApplication::app411SetPersonSearchEvent);
            break;

        case lookupResult411PersonSearch: //no break
        case lookupResult411ReversePhone:
            updateAfterLookupPersonSearch(*lookupManager);
            break;

        case lookupResult411BusinessSearch:
            updateAfterLookupBusinessSearch(*lookupManager);
            break;

        case lookupResult411BusinessSearchMultiselect:
            Application::popupForm(selectStateForm);
            sendEvent(MoriartyApplication::app411SetBusinessMultiselectEvent);
            break;

        case lookupResult411InternationalCode:
            updateAfterLookupInternational(*lookupManager);
            break;

        default:
            update();
    }

    lookupManager->handleLookupFinishedInForm(data);
}

void M411MainForm::callPhoneNumber(const String& phoneNumber)
{
    DialPhoneNumber(phoneNumber.c_str());
}

void M411MainForm::zipOrAreaSelected(UInt16 itemId)
{
    MoriartyApplication& app=application();
    Form dialog(app, wantMoveItToMemoForm);
    if (errNone != dialog.initialize())
        return;
    if (noButton == dialog.showModal())
        return;
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL!=lookupManager);
    DynStr* toMemoBody = DynStrFromCharP3(lookupManager->getLast411SearchAreaCityZip(), _T(" - "), universalDataZipAreaCity_->getItemText(itemId,zipAreaCityIndexInUDF));
    if (NULL != toMemoBody)
    {
        if (NULL==DynStrAppendCharP2(toMemoBody, _T(" - "), universalDataZipAreaCity_->getItemText(itemId,countryIndexInUDF)))
            goto Exit;
        CreateNewMemo(_T("ArsLexis"), DynStrGetCStr(toMemoBody));
    }
Exit:
    if (NULL != toMemoBody)
        DynStrDelete(toMemoBody);
}

void M411MainForm::personSelected(UInt16 itemId)
{
    MoriartyApplication& app=application();
    Form dialog(app,addressOrCallQuestionForm);
    if (errNone != dialog.initialize())
        return;
    switch(dialog.showModal())
    {
        case addressButton:
            {
                String firstName;
                String lastName = personList_->getItemText(itemId,nameIndexInUDF);
                String city = personList_->getItemText(itemId,cityIndexInUDF);
                String state;
                String zipCode;

                if (String::npos != lastName.find(_T(' ')))
                {
                    uint_t cut = lastName.rfind(_T(' '));
                    firstName.assign(lastName,0,cut);
                    lastName.erase(0,cut+1);
                }

                if (!city.empty())
                {
                    uint_t cut = city.rfind(_T(' '));
                    if (String::npos != cut)
                    {
                        zipCode.assign(city,cut+1,String::npos);
                        if (!zipCode.empty())
                        {
                            if (isDigit(zipCode[0]))
                            {
                                city.erase(cut,String::npos);
                            }
                            else
                                zipCode.clear();   
                        } 
                        cut  = city.rfind(_T(','));
                        state.assign(city,cut+2,String::npos);
                        city.erase(cut,String::npos);
                    }
                }

                if (!newAddressBookPerson
                        (firstName.c_str(),
                         lastName.c_str(),
                         personList_->getItemText(itemId,addressIndexInUDF),
                         city.c_str(),
                         state.c_str(),
                         zipCode.c_str(),
                         personList_->getItemText(itemId,phoneIndexInUDF)))
                    MoriartyApplication::alert(unableToCompeleteOperationAlert);         
            }
            break;

        case callButton:
            callPhoneNumber(personList_->getItemText(itemId,phoneIndexInUDF));
            break;
    }
}

void M411MainForm::businessSelected(UInt16 itemId)
{
    MoriartyApplication& app=application();
    Form dialog(app,addressOrCallQuestionForm);
    if (errNone != dialog.initialize())
        return;
    switch(dialog.showModal())
    {
        case addressButton:
            {
                String city = businessList_->getItemText(itemId,cityIndexInUDF);
                String state;
                String zipCode;

                if (!city.empty())
                {
                    uint_t cut = city.rfind(_T(' '));
                    if (String::npos != cut)
                    {
                        zipCode.assign(city,cut+1,String::npos);
                        if (!zipCode.empty())
                        {
                            if (isDigit(zipCode[0]))
                            {
                                city.erase(cut,String::npos);
                            }
                            else
                                zipCode.clear();   
                        } 
                        cut  = city.rfind(_T(','));
                        state.assign(city,cut+2,String::npos);
                        city.erase(cut,String::npos);
                    }
                }

                if (!newAddressBookBusiness
                        (businessList_->getItemText(itemId,nameIndexInUDF),
                         businessList_->getItemText(itemId,addressIndexInUDF),
                         city.c_str(),
                         state.c_str(),
                         zipCode.c_str(),
                         businessList_->getItemText(itemId,phoneIndexInUDF)))
                    MoriartyApplication::alert(unableToCompeleteOperationAlert);         
            }
            break;
            
        case callButton:
            callPhoneNumber(businessList_->getItemText(itemId,phoneIndexInUDF));
            break;
    }
}    

void M411MainForm::internationalCodeSelect(UInt16 itemId)
{
    MoriartyApplication& app=application();
    Form dialog(app,wantMoveItToMemoForm);
    if (errNone != dialog.initialize())
        return;
    if (yesButton == dialog.showModal())
    {
        LookupManager* lookupManager=app.lookupManager;
        assert(NULL!=lookupManager);
        DynStr* toMemoBody = DynStrFromCharP2(lookupManager->getLast411Search(LookupManager::internationalCallingCodeTitle),_T(" - "));
        if (NULL != toMemoBody)
        {
            if (1 < internationalList_->getItemElementsCount(itemId))
            {
                if (NULL == DynStrAppendCharP3(toMemoBody, internationalList_->getItemText(itemId,cityNameIndexInUDF), _T(" - "), internationalList_->getItemText(itemId,cityCodeIndexInUDF)))
                    goto Exit;
            }    
            else
            {
                if (NULL == DynStrAppendCharP(toMemoBody, internationalList_->getItemText(itemId,countryCodeIndexInUDF)))
                    goto Exit;
            }
            CreateNewMemo(_T("ArsLexis"), DynStrGetCStr(toMemoBody));
Exit:
            if (NULL != toMemoBody)
                DynStrDelete(toMemoBody);
        }
    }
}    

void M411MainForm::handleListItemSelect(UInt16 listId, UInt16 itemId)
{
    switch (displayMode())
    {
        case showSearch:
            sendEvent(MoriartyApplication::appSelect411SearchEvent, MoriartyApplication::SelectItemEventData(itemId));
            break;
            
        case dm_reverseZipCode: //no break
        case dm_reverseAreaCode: //no break
        case dm_areaCode: //no break
        case dm_zipCode: 
            zipOrAreaSelected(itemId);
            break;

        case dm_personSearch: //no break
        case dm_reversePhone: 
            personSelected(itemId);
            break;

        case dm_businessSearch:
            businessSelected(itemId);
            break;
            
        case dm_internationalCodes:
            internationalCodeSelect(itemId);
            break;

        default:
            assert(false);
    }
}

void M411MainForm::handleSearchItemSelected(uint_t item)
{
    assert(item<M411_MODULES_COUNT);
    displayModeToSetAfterLookup_ = moduleDefs_[item].displayMode_;

    //to protect from asserts when list items changes, but selection remains
    resultsList_.setSelection(noListSelection,ExtendedList::redrawNot);
    if (resultsList_.itemsCount() > 0)
        resultsList_.setTopItem(0,ExtendedList::redrawNot);

    
    //review results 
    if (displayModeToSetAfterLookup_ != displayMode_)
    {
        MoriartyApplication& app=application();
        LookupManager* lookupManager=app.lookupManager;
        assert(NULL!=lookupManager);
        switch (displayModeToSetAfterLookup_)
        {    
            case dm_zipCode:
                if (lookupManager->isLast411SearchAvailable(LookupManager::zipByCityTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_reverseZipCode:
                if (lookupManager->isLast411SearchAvailable(LookupManager::reverseZipCodeTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_reverseAreaCode:
                if (lookupManager->isLast411SearchAvailable(LookupManager::reverseAreaCodeTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_areaCode:
                if (lookupManager->isLast411SearchAvailable(LookupManager::areaCodeByCityTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_internationalCodes:
                if (lookupManager->isLast411SearchAvailable(LookupManager::internationalCallingCodeTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_reversePhone:
                if (lookupManager->isLast411SearchAvailable(LookupManager::reversePhoneTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                break;
            case dm_personSearch:
                if (lookupManager->isLast411SearchAvailable(LookupManager::personSearchTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }
                else
                {
                    if (!personList_->empty())
                    {
                        lookupManager->setLast411Search(String(), LookupManager::personSearchTitle);
                        setDisplayMode(displayModeToSetAfterLookup_);
                        return;
                    }    
                }
                break;
            case dm_businessSearch:
                if (lookupManager->isLast411SearchAvailable(LookupManager::businessSearchTitle))
                {
                    setDisplayMode(displayModeToSetAfterLookup_);
                    return;
                }    
                else
                {
                    if (!businessList_->empty())
                    {
                        lookupManager->setLast411Search(String(), LookupManager::businessSearchTitle);
                        setDisplayMode(displayModeToSetAfterLookup_);
                        return;
                    }    
                }
                break;
        }
    }    
    
    //new search
    Application::popupForm(moduleDefs_[item].formId_);
    switch (displayModeToSetAfterLookup_)
    {
        case dm_areaCode:
            sendEvent(MoriartyApplication::app411SetAreaByCityEvent);
            break;
        case dm_zipCode:
            sendEvent(MoriartyApplication::app411SetZipByCityEvent);
            break;
        case dm_internationalCodes:
            sendEvent(MoriartyApplication::app411SetInternationalCodeEvent);
            break;
        default:
            break;
    }
}

void M411MainForm::handleSelectItemEvent(const EventType& event)
{
    if (event.eType==MoriartyApplication::appSelect411SearchEvent)
    {
        const MoriartyApplication::SelectItemEventData& data=reinterpret_cast<const MoriartyApplication::SelectItemEventData&>(event.data);
        handleSearchItemSelected(data.item);
    }
}

bool M411MainForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType)
    {
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case ctlSelectEvent:
            handleControlSelect(event);
            break;
               
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;     
            
        case lstSelectEvent:
            handleListItemSelect(event.data.lstSelect.listID, event.data.lstSelect.selection);
            break;

        case MoriartyApplication::appSelect411SearchEvent:
            handleSelectItemEvent(event);
            handled = true;
            break;

        default:
            handled=MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool M411MainForm::handleKeyPress(const EventType& event)
{
    int option = ExtendedList::optionScrollPagesWithLeftRight;
    if (application().runningOnTreo600())
        option = 0;
    if (showSearch == displayMode_)
    {
        if (searchList_.handleKeyDownEvent(event, option | ExtendedList::optionFireListSelectOnCenter))
            return true;
    }
    else
    {
        if (resultsList_.handleKeyDownEvent(event, option | ExtendedList::optionFireListSelectOnCenter))
            return true;
    }
    return false;
}

int  M411MainForm::getModuleIdByMenuId(int menuId)
{
    
    for (int i=0; i<M411_MODULES_COUNT; i++)
    {
        if (menuId==moduleDefs_[i].menuId_)
            return i;
    }
    return -1;
}

bool M411MainForm::handleMenuCommand(UInt16 itemId)
{
    bool    handled;

    int moduleId = getModuleIdByMenuId(itemId);
    if (-1 != moduleId)
    {
        handleSearchItemSelected(moduleId);
        return true;
    }

    if (mainPageMenuItem==itemId)
    {
        doneButton_.hit();
        handled=true;
    }
    else
    {
        // TODO: or should we assert?
        handled=MoriartyForm::handleMenuCommand(itemId);
    }

    return handled;
}

void M411MainForm::setDisplayMode(DisplayMode displayMode)
{
    doneButton_.hide();
    backButton_.show();
    switch (displayMode)
    {
        case showSearch:
            assert(NULL != searchListDrawHandler_.get());
            resultsList_.hide();
            searchButton_.hide();
            searchList_.show();
            searchList_.focus();
            backButton_.hide();
            doneButton_.show();
            break;

        case dm_reverseAreaCode: //no break
        case dm_reverseZipCode: //no break
        case dm_areaCode: //no break
        case dm_zipCode:
            assert(NULL != universalDataZipAreaCity_);
            if (NULL==resultsListDrawHandler_.get())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(universalDataZipAreaCity_, ResultsListDrawHandler::zipAreaCityMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            if (ResultsListDrawHandler::zipAreaCityMode != resultsList_.itemHeight())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(universalDataZipAreaCity_, ResultsListDrawHandler::zipAreaCityMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            searchList_.hide();
            searchButton_.show();
            resultsList_.setItemHeight(ResultsListDrawHandler::zipAreaCityMode);
            resultsList_.show();
            resultsList_.focus();
            break;

        case dm_personSearch:  //no break
        case dm_reversePhone: 
            assert(NULL!=personList_);
            if (NULL==resultsListDrawHandler_.get())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(personList_, ResultsListDrawHandler::personMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            if (ResultsListDrawHandler::personMode!=resultsList_.itemHeight())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(personList_, ResultsListDrawHandler::personMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            searchList_.hide();
            searchButton_.show();
            resultsList_.setItemHeight(ResultsListDrawHandler::personMode);
            resultsList_.show();
            resultsList_.focus();
            break;

        case dm_businessSearch:
            assert(NULL!=businessList_);
            if (NULL==resultsListDrawHandler_.get())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(businessList_, ResultsListDrawHandler::businessMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            if (ResultsListDrawHandler::businessMode!=resultsList_.itemHeight())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(businessList_, ResultsListDrawHandler::businessMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            searchList_.hide();
            searchButton_.show();
            resultsList_.setItemHeight(ResultsListDrawHandler::businessMode);
            resultsList_.show();
            resultsList_.focus();
            break;
            
        case dm_internationalCodes:
            assert(NULL!=internationalList_);
            if (NULL==resultsListDrawHandler_.get())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(internationalList_, ResultsListDrawHandler::internationalMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            if (ResultsListDrawHandler::internationalMode!=resultsList_.itemHeight())
            {
                resultsListDrawHandler_.reset(new ResultsListDrawHandler(internationalList_, ResultsListDrawHandler::internationalMode));
                resultsList_.setCustomDrawHandler(resultsListDrawHandler_.get());
            }
            searchList_.hide();
            searchButton_.show();
            resultsList_.setItemHeight(ResultsListDrawHandler::internationalMode);
            resultsList_.show();
            resultsList_.focus();
            break;

        default:
            assert(false);
    }            
    displayMode_=displayMode;
    updateTitle();
}

