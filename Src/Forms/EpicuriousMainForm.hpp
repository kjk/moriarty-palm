#ifndef MORIARTY_EPICURIOUS_MAIN_FORM_HPP__
#define MORIARTY_EPICURIOUS_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

class EpicuriousMainForm: public MoriartyForm {

    ScrollBar scrollBar_;
    Control doneButton_;
    Field dishNameField_;
    Control searchButton_;
    FormObject graffitiState_;
    Control listButton_;
    
    ArsLexis::String lastQuery_;
    
    TextRenderer recipeRenderer_;

    void showList();
    
    void showStartPage();
    
public:

    explicit EpicuriousMainForm(MoriartyApplication& app);
    
    ~EpicuriousMainForm();

    enum DisplayMode {
        showHelpText,
        showRecipesList,
        showRecipe
    };
    
    void setDisplayMode(DisplayMode dm);
    
    DisplayMode displayMode() const
    {return displayMode_;}
    
private:
    
    DisplayMode displayMode_;

    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);
    
    void handleLookupFinished(const EventType& event);
    
    void updateAfterLookup(LookupManager& lookupManager);
    
    void handleSearch();
    
    void prepareRecipe();

protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleMenuCommand(UInt16 itemId);
    
};

#endif