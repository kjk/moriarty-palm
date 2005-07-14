#ifndef MORIARTY_FLICKR_ABOUT_FORM_HPP__
#define MORIARTY_FLICKR_ABOUT_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

class FlickrAboutForm: public MoriartyForm
{
    ScrollBar scrollBar_;
    TextRenderer    infoRenderer_;
    Control         doneButton_;

    void prepareAbout();
    
public:

    explicit FlickrAboutForm(MoriartyApplication& app);
    
//    Err initialize();

    ~FlickrAboutForm();

private:

    bool handleControlSelect(const EventType& data);

protected:

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

};

#endif // MORIARTY_FLICKR_ABOUT_FORM_HPP__