#ifndef MORIARTY_FLICKR_MAIN_FORM_HPP__
#define MORIARTY_FLICKR_MAIN_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>
#include <TextRenderer.hpp>

struct FlickrPrefs;

class FlickrMainForm: public MoriartyForm
{
    FlickrPrefs* flickrPrefs_;
    
    TextRenderer    infoRenderer_;
    Field               emailField_;
    Field               passwordField_;
    Control             hideUploadCompletedCheckbox_;
    
    List                    privacyList_;
    Control             privacyTrigger_;
    Control             friendsPhotosCheckbox_;
    Control             familyPhotosCheckbox_;
    Field               tagsField_;
    Field               descriptionField_;
        
    Control         doneButton_;

    void prepareAbout();
    
    void savePrefs();

    void reposition();
    
    void syncCheckboxes(int sel, bool regged);

public:

    explicit FlickrMainForm(MoriartyApplication& app);
    
    Err initialize();

    ~FlickrMainForm();

    enum DisplayMode {
        showBasicOptions,
        showAdvancedOptions
    };

    void setDisplayMode(DisplayMode dm);

    DisplayMode displayMode() const
    {return displayMode_;}

private:

    DisplayMode displayMode_;

    bool handleControlSelect(const EventType& data);

protected:

    void attachControls();

    bool handleOpen();

    void resize(const ArsRectangle& screenBounds);

    bool handleEvent(EventType& event);

    bool handleMenuCommand(UInt16 itemId);

};

#endif // MORIARTY_FLICKR_MAIN_FORM_HPP__