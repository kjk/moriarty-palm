#ifndef INFOMAN_DICT_SEARCH_FORM_HPP
#define INFOMAN_DICT_SEARCH_FORM_HPP

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class DictSearchForm: public MoriartyForm 
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

    DictSearchForm(MoriartyApplication& app);
    
    ~DictSearchForm();
    
    Field inputField;
    
};

#endif