#ifndef __AMAZON_ENTER_WISHLIST_FORM_HPP__
#define __AMAZON_ENTER_WISHLIST_FORM_HPP__

#include <FormObject.hpp>
#include "MoriartyForm.hpp"

class AmazonEnterWishlistForm: public MoriartyForm
{
    Field       nameField_;
    Field       emailField_;
    Field       cityField_;
    Control     stateField_;
    const ArsLexis::char_t *stateSymbol_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

public:

    AmazonEnterWishlistForm(MoriartyApplication& app):
        MoriartyForm(app, amazonEnterWishlistForm, true),
        nameField_(*this),
        emailField_(*this),
        cityField_(*this),
        stateField_(*this),
        stateSymbol_(NULL)
    {
        setFocusControlId(nameField);
    }

    ~AmazonEnterWishlistForm();

};

#endif