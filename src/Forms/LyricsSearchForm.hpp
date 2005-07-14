#ifndef __LYRICS_SEARCH_FORM_HPP__
#define __LYRICS_SEARCH_FORM_HPP__

#include "MoriartyForm.hpp"

class LyricsSearchForm: public MoriartyForm
{
    Field artistField_;
    Field titleField_;
    Field albumField_;
    Field composerField_;
    Field fullTextField_;

    void handleControlSelect(const EventType& data);

protected:

    void attachControls();

    void resize(const ArsRectangle& screenBounds);
    
    bool handleEvent(EventType& event);
    
public:

    LyricsSearchForm(MoriartyApplication& app):
        MoriartyForm(app, lyricsSearchForm, true),
        artistField_(*this),
        titleField_(*this),
        albumField_(*this),
        composerField_(*this),
        fullTextField_(*this)
    {
        setFocusControlId(titleField);
    }    
    
    ~LyricsSearchForm();

};

#endif