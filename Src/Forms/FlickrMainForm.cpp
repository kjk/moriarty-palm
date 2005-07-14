#include <Text.hpp>

#include <LineBreakElement.hpp>
#include <TextElement.hpp>

#include "../../FlickrUploader/Src/Flickr.h"

#include "MoriartyPreferences.hpp"

#include "FlickrMainForm.hpp"
#include "HyperlinkHandler.hpp"
#include "MoriartyStyles.hpp"
#include <SysUtils.hpp>

#define PASSWORD_MASK "\x95\x95\x95\x95\x95\x95\x95\x95"

FlickrMainForm::FlickrMainForm(MoriartyApplication& app):
    MoriartyForm(app, flickrMainForm),
    flickrPrefs_(NULL),
    infoRenderer_(*this, NULL),
    emailField_(*this),
    passwordField_(*this),
    hideUploadCompletedCheckbox_(*this),
    privacyTrigger_(*this),
    privacyList_(*this),
    friendsPhotosCheckbox_(*this),
    familyPhotosCheckbox_(*this),
    tagsField_(*this),
    descriptionField_(*this),
    
    doneButton_(*this),
    displayMode_(showBasicOptions)
 {
    setFocusControlId(emailField);
    infoRenderer_.setHyperlinkHandler(app.hyperlinkHandler);
    infoRenderer_.setInteractionBehavior(   
        TextRenderer::behavHyperlinkNavigation
      | TextRenderer::behavUpDownScroll
    );
}

Err FlickrMainForm::initialize()
{
    Err err = MoriartyForm::initialize();
    if (errNone != err)
        return err;
    
    flickrPrefs_ = new_nt FlickrPrefs();
    if (NULL == flickrPrefs_)
        return memErrNotEnoughSpace;
    
    memzero(flickrPrefs_, sizeof(*flickrPrefs_));
    UInt16 size = sizeof(*flickrPrefs_);
    Int16 ver = PrefGetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefs_, &size, true);
    return errNone;
}

FlickrMainForm::~FlickrMainForm() 
{
    delete flickrPrefs_;
}

void FlickrMainForm::attachControls()
{
    MoriartyForm::attachControls();
    infoRenderer_.attach(infoRenderer);

    emailField_.attach(emailField);
    passwordField_.attach(passwordField);
    hideUploadCompletedCheckbox_.attach(hideUploadCompletedCheckbox);
    privacyTrigger_.attach(privacyTrigger);
    privacyList_.attach(photoPrivacyList);
    friendsPhotosCheckbox_.attach(friendsPhotosCheckbox);
    familyPhotosCheckbox_.attach(familyPhotosCheckbox);
    tagsField_.attach(tagsField);
    descriptionField_.attach(descriptionField);
    
    doneButton_.attach(doneButton);
}

void FlickrMainForm::syncCheckboxes(int sel, bool regged)
{
    bool visible = (showAdvancedOptions == displayMode_);
    privacyTrigger_.setEnabled(regged);
    privacyTrigger_.setVisible(visible);
    FormObject object(*this, visibilityLabel);
    object.setVisible(visible);
    
    bool priv = (1 == sel);
    if (!priv) 
    {
        familyPhotosCheckbox_.setValue(0);
        friendsPhotosCheckbox_.setValue(0);
    }

    familyPhotosCheckbox_.setEnabled(priv && regged);
    friendsPhotosCheckbox_.setEnabled(priv && regged);
    familyPhotosCheckbox_.setVisible(priv && visible);
    friendsPhotosCheckbox_.setVisible(priv && visible);
    
    object.attach(visibilityPrivateLabel);
    object.setVisible(priv && visible);
}

bool FlickrMainForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    
    emailField_.setEditableText(flickrPrefs_->email, StrLen(flickrPrefs_->email));
    if (0 != StrLen(flickrPrefs_->password))
        passwordField_.setEditableText(PASSWORD_MASK, StrLen(PASSWORD_MASK));
    else
        passwordField_.setEditableText("", 0);
        
    hideUploadCompletedCheckbox_.setValue(flickrPrefs_->dontShowUploadCompletedForm ? 1 : 0);
        
    privacyList_.setSelection(flickrPrefs_->isPublic ? 0 : 1);
    privacyTrigger_.setLabel(privacyList_.selectionText());

    friendsPhotosCheckbox_.setValue(flickrPrefs_->isFriend ? 1 : 0);
    familyPhotosCheckbox_.setValue(flickrPrefs_->isFamily ? 1 : 0);
    
    syncCheckboxes(flickrPrefs_->isPublic ? 0 : 1, flickrPrefs_->registered);

    tagsField_.setEditableText(flickrPrefs_->tags, StrLen(flickrPrefs_->tags));
    descriptionField_.setEditableText(flickrPrefs_->description, StrLen(flickrPrefs_->description));
    
    setDisplayMode(displayMode());
    return result;
}

void FlickrMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
        
    setBounds(bounds = screenBounds);
    
    FormObject graffiti(*this);
    graffiti.attachByIndex(getGraffitiStateIndex());
    
    emailField_.anchor(screenBounds, anchorRightEdge, 4, anchorNot, 0);
    passwordField_.anchor(screenBounds, anchorRightEdge, 4, anchorNot, 0);
    
    infoRenderer_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 113);

    tagsField_.anchor(screenBounds, anchorRightEdge, 27, anchorNot, 0);
    
    bool regged = !application().preferences().regCode.empty();
    if (regged)
        descriptionField_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 104);
    else
        descriptionField_.anchor(screenBounds, anchorRightEdge, 4, anchorBottomEdge, 123);

    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);    
    graffiti.anchor(screenBounds, anchorLeftEdge, 10, anchorTopEdge, 12);
    update();    
}

bool FlickrMainForm::handleEvent(EventType& event)
{
    if (showBasicOptions == displayMode_ && infoRenderer_.handleEventInForm(event))
        return true;

    MoriartyApplication& app = application();

    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelect(event);
            break;
            
        case popSelectEvent: 
            syncCheckboxes(event.data.popSelect.selection, !app.preferences().regCode.empty());
            break;
                    
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool FlickrMainForm::handleMenuCommand(UInt16 itemId)
{
    MoriartyApplication& app = application();
    LookupManager& lm = *app.lookupManager;

    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            return true;

        default:
            assert(false);
    }
    return false;
}

void FlickrMainForm::reposition()
{
    bool regged = !application().preferences().regCode.empty();
    FormObject object(*this);

    RectangleType rect;
    getScreenBounds(rect);

    if (regged)
    {
        object.attach(visibilityLabel);
        object.setTopLeft(2, 30);
        privacyList_.setTopLeft(66, 30);
        privacyTrigger_.setTopLeft(52, 30);
        object.attach(visibilityPrivateLabel);
        object.setTopLeft(2, 44);
        friendsPhotosCheckbox_.setTopLeft(46, 44);
        familyPhotosCheckbox_.setTopLeft(96, 44);
        object.attach(tagsLabel);
        object.setTopLeft(2, 58);
        tagsField_.setTopLeft(25, 58);
        object.attach(descriptionLabel);
        object.setTopLeft(2, 72);
        descriptionField_.setTopLeft(2, 86);
        descriptionField_.anchor(ArsRectangle(rect), anchorRightEdge, 4, anchorBottomEdge, 104);
    }    
    else
    {
        object.attach(visibilityLabel);
        object.setTopLeft(2, 52);
        privacyList_.setTopLeft(66, 52);
        privacyTrigger_.setTopLeft(52, 52);
        object.attach(visibilityPrivateLabel);
        object.setTopLeft(2, 65);
        friendsPhotosCheckbox_.setTopLeft(46, 65);
        familyPhotosCheckbox_.setTopLeft(96, 65);
        object.attach(tagsLabel);
        object.setTopLeft(2, 79);
        tagsField_.setTopLeft(25, 79);
        object.attach(descriptionLabel);
        object.setTopLeft(2, 93);
        descriptionField_.setTopLeft(2, 105);
        descriptionField_.anchor(ArsRectangle(rect), anchorRightEdge, 4, anchorBottomEdge, 123);
       
    }
    syncCheckboxes(privacyList_.selection(), regged);
    tagsField_.setReadOnly(!regged);
    descriptionField_.setReadOnly(!regged);
}

void FlickrMainForm::setDisplayMode(DisplayMode dm)
{
    Control control(*this);
    FormObject object(*this);
    bool regged = !application().preferences().regCode.empty();
    switch (displayMode_=dm)
    {
        case showBasicOptions:
            control.attach(basicOptionsButton);
            control.setValue(1);
            object.attach(visibilityLabel);
            object.hide();
            privacyTrigger_.hide();
            object.attach(visibilityPrivateLabel);
            object.hide();
            friendsPhotosCheckbox_.hide();
            familyPhotosCheckbox_.hide();
            object.attach(tagsLabel);
            object.hide();
            tagsField_.hide();
            object.attach(descriptionLabel);
            object.hide();
            descriptionField_.hide();
            object.attach(registerToEnable1Label);
            object.hide();
            object.attach(registerToEnable2Label);
            object.hide();
            
            if (infoRenderer_.empty())
                prepareAbout();
            infoRenderer_.show();
            object.attach(emailLabel);
            object.show();
            emailField_.show();
            object.attach(passwordLabel);
            object.show();
            passwordField_.show();
            hideUploadCompletedCheckbox_.show();
            break;

        case showAdvancedOptions:
            infoRenderer_.hide();
            object.attach(emailLabel);
            object.hide();
            emailField_.hide();
            object.attach(passwordLabel);
            object.hide();
            passwordField_.hide();
            hideUploadCompletedCheckbox_.hide();

            object.attach(registerToEnable1Label);
            if (regged)
                object.hide();
            else
                object.show();
                                
            object.attach(registerToEnable2Label);
            if (regged)
                object.hide();
            else
                object.show();

            reposition();

            control.attach(advancedOptionsButton);
            control.setValue(1);
            object.attach(visibilityLabel);
            object.show();

            privacyTrigger_.show();
            object.attach(tagsLabel);
            object.show();
            tagsField_.show();
            object.attach(descriptionLabel);
            object.show();
            descriptionField_.show();
            break; 

        default:
            assert(false);
    }
}

void FlickrMainForm::savePrefs()
{
    const char* text = emailField_.text();
    StrNCopy(flickrPrefs_->email, text, FlickrPrefs::maxEmailLength);
    flickrPrefs_->email[FlickrPrefs::maxEmailLength] = chrNull;
    
    text = passwordField_.text();
    if (0 != StrCompare(PASSWORD_MASK, text))
    {
        StrNCopy(flickrPrefs_->password, text, FlickrPrefs::maxPasswordLength);
        flickrPrefs_->password[FlickrPrefs::maxPasswordLength] = chrNull;
    }
    
    flickrPrefs_->dontShowUploadCompletedForm = (1 == hideUploadCompletedCheckbox_.value());

    Preferences& prefs = application().preferences();
    flickrPrefs_->registered = !prefs.regCode.empty();
    if (flickrPrefs_->registered)
    {
        flickrPrefs_->useCustomPrivacySettings = true; // (1 == overrideDefaultPrivacySettingsCheckbox_.value());
        flickrPrefs_->isPublic = (0 == privacyList_.selection());
        flickrPrefs_->isFriend = (1 == friendsPhotosCheckbox_.value());
        flickrPrefs_->isFamily = (1 == familyPhotosCheckbox_.value());
        
        text = descriptionField_.text();
        StrNCopy(flickrPrefs_->description, text, FlickrPrefs::maxDescriptionLength);
        flickrPrefs_->description[FlickrPrefs::maxDescriptionLength] = chrNull;
        
        text = tagsField_.text();
        StrNCopy(flickrPrefs_->tags, text, FlickrPrefs::maxTagsLength);
        flickrPrefs_->tags[FlickrPrefs::maxTagsLength] = chrNull;
    }
    PrefSetAppPreferences(FlickrCreatorID, flickrPrefsResourceID, flickrPrefsVersion, flickrPrefs_, sizeof(*flickrPrefs_), true);
}

bool FlickrMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            savePrefs();
            application().runMainForm();
            return true;

        case advancedOptionsButton:
            if (showAdvancedOptions != displayMode_)
            {
                setDisplayMode(showAdvancedOptions);
                update();
            }
            return false;   
     
        case basicOptionsButton:
            if (showBasicOptions != displayMode_)
            {
                setDisplayMode(showBasicOptions);
                update();
            }
            return false;

    }
    return false;
}

void FlickrMainForm::prepareAbout()
{
    infoRenderer_.clear();

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    DefinitionModel::Elements_t& elems = model->elements;
    
    TextElement* text = new_nt TextElement("Flickr.com is an on-line photo sharing site. InfoMan allows posting photos directly from your device to your flickr account. ");
    elems.push_back(text);
    text->setStyle(StyleGetStaticStyle(styleNameGray));

    text = new_nt TextElement("Learn more");
    elems.push_back(text);
    text->setHyperlink(urlSchemaFlickr urlSeparatorSchemaStr flickrUrlPartAbout, hyperlinkUrl);

    text = new_nt TextElement(".");
    elems.push_back(text);
    text->setStyle(StyleGetStaticStyle(styleNameGray));
    
    infoRenderer_.setModel(model, Definition::ownModel);
    return;
}
