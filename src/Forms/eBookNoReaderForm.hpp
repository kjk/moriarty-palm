#ifndef EBOOK_NO_READER_FORM_HPP__
#define EBOOK_NO_READER_FORM_HPP__

#include "MoriartyForm.hpp"
#include <FormObject.hpp>

class EBookNoReaderForm: public MoriartyForm {

    Control     downloadButton_;
    Control     cancelButton_;
    Control     dontAskAgainCheckbox_;
    
public:

    EBookNoReaderForm(MoriartyApplication& app);
    
    ~EBookNoReaderForm();
    
protected:

    void attachControls();

    bool handleEvent(EventType& event);
    
    bool handleControlSelected(const EventType& event);
    
private:

    void handleDownloadButton();
   
};

#endif // EBOOK_NO_READER_FORM_HPP__