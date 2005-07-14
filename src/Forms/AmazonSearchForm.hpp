#ifndef __AMAZON_SEARCH_FORM_HPP__
#define __AMAZON_SEARCH_FORM_HPP__

#include "MoriartyForm.hpp"
#include <TextRenderer.hpp>
#include <DynStr.hpp>

class AmazonSearchForm: public MoriartyForm
{
    TextRenderer textRenderer_;

    Field       searchField_;
    Control     okButton_;
    Control     cancelButton_;
    FormObject  graffitiState_;    

    // holds a pointer to requestString given in constructor. Doesn't make a copy
    // so don't free it. We assume requestString will be valid through the form
    // lifetime
    const ArsLexis::char_t *request_;
        
    void handleControlSelect(const EventType& data);

    void afterFormOpen();
    
protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
    bool handleOpen();
        
public:

    AmazonSearchForm(MoriartyApplication& app, const char_t* requestString, const char_t* displayText);
    
    ~AmazonSearchForm();
    
};

#endif