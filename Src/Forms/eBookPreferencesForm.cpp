#include "EBookPreferencesForm.hpp"
#include "MoriartyPreferences.hpp"
#include <SysUtils.hpp>
#include "eBookFormats.hpp"

struct CheckboxMapping {
    UInt16 id;
    const char* formatName;
};

static const CheckboxMapping checkboxMappings[] = {
    {ebookFormat_Doc_Checkbox,                  eBookFormatName_Doc},
    {ebookFormat_eReader_Checkbox,            eBookFormatName_eReader},
    {ebookFormat_iSilo_Checkbox,                  eBookFormatName_iSilo},
    {ebookFormat_iSiloX_Checkbox,                eBookFormatName_iSiloX},
    {ebookFormat_zTXT_Checkbox,                  eBookFormatName_zTXT}
};

EBookPreferencesForm::EBookPreferencesForm(MoriartyApplication& app):
    MoriartyForm(app, ebookPreferencesForm, true),
    okButton_(*this),
    cancelButton_(*this),
    downloadDestinationList_(*this),
    downloadDestinations_(NULL),
    downloadDestinationsSize_(0),
    volumeCount_(0),
    volumes_(NULL)
{}

EBookPreferencesForm::~EBookPreferencesForm() 
{
    StrArrFree(downloadDestinations_, downloadDestinationsSize_);
    if (NULL != volumes_)
        free(volumes_);
}

void EBookPreferencesForm::attachControls()
{
    MoriartyForm::attachControls();
    okButton_.attach(okButton);
    cancelButton_.attach(cancelButton);
    downloadDestinationList_.attach(downloadDestinationList);
}

bool EBookPreferencesForm::handleOpen()
{
    bool result = MoriartyForm::handleOpen();
    const EBookPreferences& prefs = application().preferences().ebookPrefs;
    Control checkbox(*this);
    
    ulong_t selectedVolumeIndex = 0;
    static const ulong_t maxVolumeCount = 8;
    downloadDestinations_ = StrArrCreate(maxVolumeCount);
    if (NULL == downloadDestinations_)
        return result;
    downloadDestinationsSize_ = maxVolumeCount;
    
   volumes_ = (UInt16*)malloc(sizeof(UInt16) * maxVolumeCount);
   if (NULL == volumes_)
        return result;
   
    downloadDestinations_[0] = StringCopy2("Main memory");
    if (NULL != downloadDestinations_[0])
        volumes_[volumeCount_++] = vfsVolumeMainMemory;

    if (VFS_FeaturesPresent())
    {
        CDynStr str;
        UInt16 ref;
        UInt32 iterator = vfsIteratorStart;

        char* label = (char*)malloc(256);
        if (NULL == label)
            goto Finish;
        
        UInt32 i = 0;            
        while (vfsIteratorStop != iterator)
        {
            ++i;
            Err err = VFSVolumeEnumerate(&ref, &iterator);
            if (errNone != err)
            {
                if (expErrEnumerationEmpty == err)
                    break;
                else
                    continue;
            }
            label[0] = chrNull;
            err = VFSVolumeGetLabel(ref, label, 256);
            if (errNone != err)
                continue;

            if ('\0' == *label)
                StrPrintF(label, "[Volume %ld]", i);
            
            // \x1a is chrCardIcon
            if (NULL == str.AppendCharP2("\x1a ", label))
                continue;

            assert(volumeCount_ < maxVolumeCount);
            volumes_[volumeCount_] = ref;
            if (prefs.targetVfsVolume == ref)
                selectedVolumeIndex = volumeCount_;
            downloadDestinations_[volumeCount_++] = str.ReleaseStr();
        }
        free(label);
    }
    
    for (uint_t i = 0; i < ARRAY_SIZE(checkboxMappings); ++i)
    {
        checkbox.attach(checkboxMappings[i].id);
        if (-1 != StrFind(prefs.requestedFormats, -1, checkboxMappings[i].formatName, -1))
            checkbox.setValue(1);
        else
            checkbox.setValue(0);
    }
    
Finish:
    downloadDestinationList_.setChoices(downloadDestinations_, volumeCount_);
    downloadDestinationList_.setVisibleItemsCount(volumeCount_);
    if (selectedVolumeIndex < volumeCount_)
    {
        downloadDestinationList_.setSelection(selectedVolumeIndex);
        Control trigger(*this, downloadDestinationPopupTrigger);
        trigger.setLabel(downloadDestinations_[selectedVolumeIndex]);
    }
    return result;
}

bool EBookPreferencesForm::handleEvent(EventType& event)
{
    bool handled = false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handled = handleControlSelected(event);
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool EBookPreferencesForm::handleControlSelected(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case okButton:
            handleOkButton();
            return true;

        case cancelButton:
            closePopup();
            return true;
            
        case downloadDestinationPopupTrigger:
            break;
            
        default:
            assert(false);
    }
    return false;
}

void EBookPreferencesForm::handleOkButton()
{
    EBookPreferences& prefs = application().preferences().ebookPrefs;
    CDynStr str;
    Control checkbox(*this);
    for (uint_t i = 0; i < ARRAY_SIZE(checkboxMappings); ++i)
    {
        checkbox.attach(checkboxMappings[i].id);
        if (checkbox.value())
        {
            if (0 != str.Len())
                str.AppendCharP(" ");
            str.AppendCharP(checkboxMappings[i].formatName);
        }               
    }
    char* newStr = str.ReleaseStr();
    if (NULL == newStr)
        newStr = StringCopy2("");
    if (NULL == newStr)
    {
        MoriartyApplication::alert(notEnoughMemoryAlert);
        closePopup();
        return;
    }

    prefs.replaceRequestedFormats(newStr);    
  
    assert(volumeCount_ == downloadDestinationList_.itemsCount());
    prefs.targetVfsVolume = volumes_[downloadDestinationList_.selection()];
    closePopup();
}


