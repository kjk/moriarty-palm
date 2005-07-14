#ifndef MORIARTY_TEST_WIKI_MAIN_FORM_HPP__
#define MORIARTY_TEST_WIKI_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

class HyperlinkHandler;

class TestWikiMainForm: public MoriartyForm {

    ScrollBar scrollBar_;
    Control doneButton_;
    Control nextButton_;
    
    TextRenderer txtRenderer_;
    
    int actTest_;
    int testsCount_;
    
    String title_;
    
public:

    explicit TestWikiMainForm(MoriartyApplication& app);
    
    ~TestWikiMainForm();
    
    void showMenu(const char_t* txt, long len, const Point& point);

private:

    void selectText();

    void parseText(int recNo);

    int showStringListForm(char_t* strList[], int strListSize);
    
    void handleControlSelect(const EventType& data);
    
    bool handleKeyPress(const EventType& event);

    void handleNextButton();
    
protected:

    void attachControls();

    bool handleOpen();
    
    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
};

#endif
