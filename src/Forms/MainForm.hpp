#ifndef MORIARTY_MAIN_FORM_HPP__
#define MORIARTY_MAIN_FORM_HPP__

#include "MoriartyApplication.hpp"
#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <ExtendedList.hpp>
#include <HmStyleList.hpp>
#include <TextRenderer.hpp>
#include <Table.hpp>

class MainForm: public MoriartyForm {

public:

    MainForm(MoriartyApplication& app);
    
    ~MainForm();

private:

    HmStyleList     smallModulesList_;
    ScrollBar       scrollBar_;
    ScrollBar       tableScrollBar_;
    TextRenderer    textRenderer_;
    Table           smallModulesTable_;

    UInt32           lastKeyPressedTime_;
    ArsLexis::String pressedKeys_;
    int              repeatCount_;

    bool ignoreEvents_;

    typedef std::auto_ptr<ExtendedList::CustomDrawHandler> DrawHandlerPtr;
    DrawHandlerPtr smallListDrawHandler_;
    
    void handleListItemSelect(uint_t listId, uint_t itemId);
    
    ExtendedList& currentList()
    {return smallModulesList_;}
    
    void updateTitle();

    int showStringListForm(ArsLexis::char_t* strList[], int strListSize);

    bool handleKeyPressed(ArsLexis::char_t key);

#ifndef SHIPPING
    void changeServer();
#endif

    void prepareRenderer();

    void prepareTable();
    
    void setDisplayModeFromPreferences();
    
protected:

    enum DisplayMode {
        showSmallModulesList,
        showSmallModulesTable,
        showTextRenderer
    };

private:

    DisplayMode displayMode_;
    
protected:
    
    void attachControls();

    bool handleMenuCommand(UInt16 itemId);

    bool handleUpdate(UInt16 updateCode);

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);
    
    void setDisplayMode(DisplayMode mode);
    
    DisplayMode displayMode() const
    {return displayMode_;}
    
};

#endif
