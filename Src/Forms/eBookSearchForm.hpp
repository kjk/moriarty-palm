#ifndef INFOMAN_PEDIA_SEARCH_FORM_HPP__
#define INFOMAN_PEDIA_SEARCH_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class EBookSearchForm: public MoriartyForm 
{
protected:

    void attachControls();
    
    bool handleEvent(EventType& event);
    
//    void resize(const ArsRectangle& rect);

public:

    // This string is not owned by form. EBookSearchForm only references it
    // but won't free etc.
    const char_t* searchPhrase;

    EBookSearchForm(MoriartyApplication& app);
    
    ~EBookSearchForm();
    
    Field inputField;
    
};

#endif