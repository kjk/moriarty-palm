#ifndef __M411_MAINFORM_HPP__
#define __M411_MAINFORM_HPP__

#include <Graphics.hpp>
#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <HmStyleList.hpp>
#include <UniversalDataFormat.hpp>

class LookupManager;

#define personSearchTxt        "Person search"
#define businessSearchTxt      "Business search"
#define reversePhoneTxt        "Reverse phone"
#define zipCodeTxt             "Zip code"
#define reverseZipCodeTxt      "Reverse zip code"
#define areaCodeTxt            "Area code"
#define reverseAreaCodeTxt     "Reverse area code"
#define internationalCodesTxt  "International code search"

#define MAX_M411_MODULE_NAME sizeof(internationalCodesTxt)

#define M411_MODULES_COUNT 8

class M411MainForm: public MoriartyForm
{
    UniversalDataFormat* universalDataZipAreaCity_;
    UniversalDataFormat* personList_;
    UniversalDataFormat* businessList_;
    UniversalDataFormat* internationalList_;

    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> ListDrawHandlerPtr;
    ListDrawHandlerPtr searchListDrawHandler_;
    ListDrawHandlerPtr resultsListDrawHandler_;
    
    HmStyleList searchList_;
    HmStyleList resultsList_;
    Control searchButton_;
    Control doneButton_;
    Control backButton_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void setControlsState(bool enabled);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);

    void updateAfterLookupPersonSearch(LookupManager& lookupManager);

    void updateAfterLookupBusinessSearch(LookupManager& lookupManager);

    void updateAfterLookupInternational(LookupManager& lookupManager);
    
    void handleListItemSelect(UInt16 listId, UInt16 itemId);
    
    void handleSelectItemEvent(const EventType& event);

    void handleSearchItemSelected(uint_t item);

    void callPhoneNumber(const ArsLexis::String& phoneNumber);
    
    void zipOrAreaSelected(UInt16 itemId);
    
    void personSelected(UInt16 itemId);
    
    void businessSelected(UInt16 itemId);
    
    void internationalCodeSelect(UInt16 itemId);
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);

    void updateTitle(void);

public:
    
    M411MainForm(MoriartyApplication& app);
    
    ~M411MainForm();

    public:
        // we use a convention for naming:
        // display mode is dm_foo and corresponding menu item
        // is fooMenuItem. This allows us to use macros to shorten the code
        enum DisplayMode
        {
            showSearch,
            dm_personSearch,
            dm_businessSearch,
            dm_reversePhone,
            dm_zipCode,
            dm_reverseZipCode,
            dm_areaCode,
            dm_reverseAreaCode,
            dm_internationalCodes
        };
    
        typedef struct m411ModuleDef_ {
          ArsLexis::char_t    name_[MAX_M411_MODULE_NAME];
          int                 formId_;
          DisplayMode         displayMode_;
          int                 menuId_;
        } m411ModuleDef_t;
    
    DisplayMode displayMode() const
    {return displayMode_;}

    void setDisplayMode(DisplayMode displayMode);

private:
    static m411ModuleDef_t moduleDefs_[M411_MODULES_COUNT];
    int getModuleIdByMenuId(int menuId);

private:
    
    DisplayMode displayMode_;
    DisplayMode displayModeToSetAfterLookup_;
  
};

#endif
