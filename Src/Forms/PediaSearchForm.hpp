#ifndef INFOMAN_PEDIA_SEARCH_FORM_HPP__
#define INFOMAN_PEDIA_SEARCH_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class PediaSearchForm: public MoriartyForm 
{
    Control searchButton_;
    
protected:

    void attachControls();
    
    bool handleEvent(EventType& event);
    
    void resize(const ArsRectangle& rect);

public:

    // This string is not owned by form. PediaSearchForm only references it
    // but won't free etc.
    const char_t* searchTerm;

    PediaSearchForm(MoriartyApplication& app);
    
    ~PediaSearchForm();
    
    Field inputField;
    
};

#endif