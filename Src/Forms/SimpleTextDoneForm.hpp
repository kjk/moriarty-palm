#ifndef MORIARTY_SIMPLE_TEXT_DONE_FORM_HPP__
#define MORIARTY_SIMPLE_TEXT_DONE_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>
#include <DynStr.hpp>

class Definition;

class SimpleTextDoneForm: public MoriartyForm {

    ScrollBar scrollBar_;
    Control doneButton_;

    TextRenderer textRenderer_;

    DynStr*          titleString_;    
    int              index_;
    int              level_;
    
public:

    enum DisplayMode {
        showNothing,
        showGasPricesDetails,
        showAboutMain,
        showAboutHowToRegister,
        showSerializedDefinition
    };

    explicit SimpleTextDoneForm(MoriartyApplication& app, DisplayMode dm, int index, int level = 0);

    explicit SimpleTextDoneForm(MoriartyApplication& app, const char_t* title, const char_t* definition);
    
    ~SimpleTextDoneForm();

    void setDisplayMode(DisplayMode displayMode);
    
private:
    
    DisplayMode displayMode_;
    
    void handleControlSelect(const EventType& data);

    bool handleKeyPress(const EventType& event);

    void prepareGasPricesDetails();

    void prepareAboutMain();

    void prepareAboutHowToRegister();

protected:
    
    bool handleOpen();

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
};

#endif
