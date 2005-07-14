#include "EpicuriousMainForm.hpp"
#include "MoriartyPreferences.hpp"
#include "LookupManager.hpp"
#include <Definition.hpp>
#include <TextElement.hpp>
#include <LineBreakElement.hpp>
#include <Text.hpp>
#include <SysUtils.hpp>
#include <ByteFormatParser.hpp>
#include <HyperlinkHandler.hpp>

#include "MoriartyStyles.hpp"

enum {
    recipeNameIndex,
    recipeInfoIndex,
    recipeIngredientsIndex,
    recipePreperationIndex,
    recipeNoteIndex,
    recipeTupleItemsCount
};

enum {   
    reviewPersonIndex,
    reviewDateIndex,
    reviewNoteIndex,
    reviewTextIndex, 
    reviewTupleItemsCount
};

EpicuriousMainForm::EpicuriousMainForm(MoriartyApplication& app):
    MoriartyForm(app, epicuriousMainForm),
    scrollBar_(*this),
    doneButton_(*this),
    dishNameField_(*this),
    searchButton_(*this),
    displayMode_(showHelpText),
    graffitiState_(*this),
    listButton_(*this),
    recipeRenderer_(*this, &scrollBar_)
{
    recipeRenderer_.setInteractionBehavior(
        TextRenderer::behavUpDownScroll
      | TextRenderer::behavMenuBarCopyButton
      | TextRenderer::behavMouseSelection
      | TextRenderer::behavHyperlinkNavigation
    );  
 
    recipeRenderer_.setHyperlinkHandler(app.hyperlinkHandler);

}

EpicuriousMainForm::~EpicuriousMainForm() {}

void EpicuriousMainForm::attachControls()
{
    MoriartyForm::attachControls();
    scrollBar_.attach(definitionScrollBar);
    doneButton_.attach(doneButton);
    dishNameField_.attach(dishNameField);
    searchButton_.attach(searchButton);
    recipeRenderer_.attach(recipeRenderer);
    recipeRenderer_.setNavOrderOptions(TextRenderer::navOrderFirst);
    
    listButton_.attach(listButton);
    
    graffitiState_.attachByIndex(getGraffitiStateIndex());
}

bool EpicuriousMainForm::handleOpen()
{
    bool result=MoriartyForm::handleOpen();
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(NULL != lookupManager);
    
    if (!lookupManager->recipe.empty())
        setDisplayMode(showRecipe);
    else if (!lookupManager->recipeMetrics.empty())
        setDisplayMode(showRecipesList);
    else
        setDisplayMode(displayMode_);

    return result;
}

void EpicuriousMainForm::resize(const ArsRectangle& screenBounds)
{
    ArsRectangle bounds;
    this->bounds(bounds);
    if (screenBounds == bounds)
        return;
    setBounds(bounds = screenBounds);

    bounds.explode(0, 17, 0, -37);

    recipeRenderer_.anchor(screenBounds, anchorRightEdge, 8, anchorBottomEdge, 36);
    scrollBar_.anchor(screenBounds, anchorLeftEdge, 7, anchorBottomEdge, 36);
    
    doneButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    listButton_.anchor(screenBounds, anchorNot, 0, anchorTopEdge, 14);
    dishNameField_.anchor(screenBounds, anchorRightEdge, 96, anchorTopEdge, 14);
    searchButton_.anchor(screenBounds, anchorLeftEdge, 44, anchorTopEdge, 14);
    graffitiState_.anchor(screenBounds, anchorLeftEdge, 55, anchorTopEdge, 12);
    
    update();    
}

bool EpicuriousMainForm::handleEvent(EventType& event)
{
    if (recipeRenderer_.handleEventInForm(event))
        return true;

    bool handled=false;
    switch (event.eType) 
    {
        case ctlSelectEvent:
            handleControlSelect(event);
            handled = true;
            break;
            
        case keyDownEvent:
            handled = handleKeyPress(event);
            break;

        case MoriartyApplication::appRecipePartsChangedEvent:
            if (!application().lookupManager->recipe.empty())
                if (showRecipe == displayMode_)
                {
                    prepareRecipe();
                    update();
                }    
            break;
            
        case LookupManager::lookupFinishedEvent:
            handleLookupFinished(event);
            handled = true;
            break;
            
        default:
            handled = MoriartyForm::handleEvent(event);
    }
    return handled;
}

bool EpicuriousMainForm::handleMenuCommand(UInt16 itemId)
{
    bool handled = false;
    switch (itemId)
    {
        case mainPageMenuItem:
            doneButton_.hit();
            handled = true;
            break;
            
        case viewRecipeMenuItem:
            if (showRecipe == displayMode_)
                break;
            LookupManager* lookupManager = application().lookupManager;
            assert(NULL != lookupManager);
            if (0 != lookupManager->recipe.getItemsCount())
            {
                setDisplayMode(showRecipe);
                update();
            }
            break;
            
        case viewRecipesListMenuItem:
            listButton_.hit();
            break;
            
        case epicuriousPreferencesMenuItem:
            Application::popupForm(epicuriousPreferencesForm);
            break;
            
        default:
            assert(false);
    }
    return handled;
}
   
void EpicuriousMainForm::setDisplayMode(EpicuriousMainForm::DisplayMode dm)
{
    switch (displayMode_=dm)
    {
        case showRecipesList:
            listButton_.hide();
            dishNameField_.show();
            graffitiState_.show();
            searchButton_.show();
            doneButton_.show();
            showList();
            break;
            
        case showRecipe:
            doneButton_.hide();
            searchButton_.hide();
            dishNameField_.hide();
            graffitiState_.hide();
            listButton_.show();
            listButton_.focus();
            prepareRecipe();
            break;  
            
        case showHelpText:
            listButton_.hide();
            searchButton_.show();
            dishNameField_.show();
            graffitiState_.show();
            dishNameField_.focus();
            doneButton_.show();
            showStartPage();
            break;
            
        default:
            assert(false);
    }
}

void EpicuriousMainForm::handleSearch()
{
    const char* dishName = dishNameField_.text();
    if (NULL == dishName)
        return;
    if (0 == lastQuery_.compare(dishName))
    {
        if (showRecipesList != displayMode_)
        {
            setDisplayMode(showRecipesList);
            update();
        }
        return;
    }
    LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);
    
    lastQuery_.assign(_T("s+recipeslist:")).append(dishName);
    lookupManager->fetchUrl(lastQuery_.c_str());
    lastQuery_.assign(dishName);
}

void EpicuriousMainForm::handleControlSelect(const EventType& event)
{
    switch (event.data.ctlSelect.controlID)
    {
        case doneButton:
            application().runMainForm();
            break;
            
        case searchButton:
            handleSearch();
            break;
            
        case listButton:
            if (showRecipesList == displayMode_)
                break;
            setDisplayMode(showRecipesList);
            update();
            break;

        default:
            assert(false);
    }
}

void EpicuriousMainForm::prepareRecipe()
{
    const Preferences::EpicuriousPreferences& prefs = application().preferences().epicuriousPreferences; 
    
    const LookupManager* lookupManager=application().lookupManager;
    assert(0!=lookupManager);

    const UniversalDataFormat& recipe=lookupManager->recipe;
    assert(!recipe.empty());

    DefinitionModel* model = new_nt DefinitionModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }

    Definition::Elements_t& elems = model->elements;
    TextElement* text;
    if (prefs.fDisplayRecipePart[prefs.recipeName])
    {
        elems.push_back(text=new TextElement(recipe.getItemText(0, recipeNameIndex)));
        text->setStyle(StyleGetStaticStyle(styleNameBold));
        text->setJustification(DefinitionElement::justifyCenter);
    
        elems.push_back(new LineBreakElement());
        elems.push_back(new LineBreakElement());
    }    

    String str;
    if (prefs.fDisplayRecipePart[prefs.recipeNote])
    {
        str = recipe.getItemText(0, recipeInfoIndex);
        if (! str.empty())
        {
            // avoid displaying huge empty space due to line breaks
            // if we don't have recipe info
            // TODO: maybe the test for empty string should be more
            // sophisticated
            parseSimpleFormatting(elems, str);
            elems.push_back(new LineBreakElement());
            elems.push_back(new LineBreakElement());
        }
    }    

    if (prefs.fDisplayRecipePart[prefs.recipeIngredients])
    {
        elems.push_back(text=new TextElement(_T("Ingredients")));
        text->setStyle(StyleGetStaticStyle(styleNameHeader));
        elems.push_back(new LineBreakElement());

        str = recipe.getItemText(0, recipeIngredientsIndex);
        parseSimpleFormatting(elems, str);
        elems.push_back(new LineBreakElement());
        elems.push_back(new LineBreakElement());
    }    

    if (prefs.fDisplayRecipePart[prefs.recipePreperation])
    {
        elems.push_back(text=new TextElement(_T("Preparation")));
        text->setStyle(StyleGetStaticStyle(styleNameHeader));
        elems.push_back(new LineBreakElement());

        str = recipe.getItemText(0, recipePreperationIndex);
        parseSimpleFormatting(elems, str);
        elems.push_back(new LineBreakElement());
        elems.push_back(new LineBreakElement());
    }    

    if (prefs.fDisplayRecipePart[prefs.recipeReviews])
    {
        uint_t itemsCount = recipe.getItemsCount();
        if (1 < itemsCount)
        {
            elems.push_back(text=new TextElement(_T("Reviews")));
            text->setStyle(StyleGetStaticStyle(styleNameHeader));
            elems.push_back(new LineBreakElement());
        }
        
        for (uint_t i = 1; i < itemsCount; ++i) 
        {
            str="Reviewed by: ";
            str.append(recipe.getItemText(i, reviewPersonIndex));
            elems.push_back(text=new TextElement(str));
            elems.push_back(new LineBreakElement());
            str="Review: ";
            str.append(recipe.getItemText(i, reviewTextIndex));
            elems.push_back(text=new TextElement(str));
            elems.push_back(new LineBreakElement());
            str="Review date: ";
            str.append(recipe.getItemText(i, reviewDateIndex));
            elems.push_back(text=new TextElement(str));
            elems.push_back(new LineBreakElement());
            long note;
            const char_t* noteText = recipe.getItemText(i, reviewNoteIndex);
            status_t error = numericValue(noteText, noteText+tstrlen(noteText), note);
            if (errNone == error && note != 0)
            {
                str="Note: ";
                str.append(noteText);
                elems.push_back(text=new TextElement(str));
                elems.push_back(new LineBreakElement());
            }            
            elems.push_back(new LineBreakElement());
        }
    }    

    if (prefs.fDisplayRecipePart[prefs.recipeGlobalNote])
    {
        elems.push_back(text=new TextElement(_T("Global note")));
        text->setStyle(StyleGetStaticStyle(styleNameHeader));
        elems.push_back(new LineBreakElement());
        elems.push_back(text=new TextElement(recipe.getItemText(0, recipeNoteIndex)));
    }
    recipeRenderer_.setModel(model, Definition::ownModel);
}


void EpicuriousMainForm::handleLookupFinished(const EventType& event)
{
    const LookupFinishedEventData& data=reinterpret_cast<const LookupFinishedEventData&>(event.data);
    switch (data.result)
    {
        case lookupResultRecipesList:
            showList();
            MoriartyApplication::touchModule(moduleIdRecipes);
            break;
            
        case lookupResultRecipe:
            prepareRecipe();
            setDisplayMode(showRecipe);
            update();
            break;
    }
    MoriartyApplication& app=application();
    LookupManager* lookupManager=app.lookupManager;
    assert(0!=lookupManager);
    lookupManager->handleLookupFinishedInForm(data);
}

bool EpicuriousMainForm::handleKeyPress(const EventType& event)
{
    switch (event.data.keyDown.chr)
    {
        case chrLineFeed:
        case chrCarriageReturn:
            searchButton_.hit();
            return true;
    }
    return false;
}

void EpicuriousMainForm::showStartPage()
{
    UInt32  dataLen;
    char_t  *data = getDataResource(recipesStartPageText, &dataLen);
    if (NULL == data)
        return;

    ByteFormatParser parser;
    parser.parseAll(data, dataLen);
    assert(NULL != data);
    free(data);

    DefinitionModel* model = parser.releaseModel();
    if (NULL == model)
    {
        application().alert(notEnoughMemoryAlert);
        return;
    }
    recipeRenderer_.setModel(model, Definition::ownModel);            
    update();
}
    
void EpicuriousMainForm::showList()
{
    UniversalDataFormat* udf = &application().lookupManager->recipeMetrics;
    if (udf->empty())
    {
        setDisplayMode(showHelpText);
        return;
    }

    for (int i=0; i < udf->getItemsCount(); i++)
    {
        switch (udf->getItemText(i,0)[0])
        {
            case _T('D'): // definition
            {
                Definition::Elements_t elems;
                ByteFormatParser parser;
                const char_t *data;
                ulong_t dataLen;
                data = udf->getItemTextAndLen(i, 1, &dataLen);
                parser.parseAll(data, dataLen);
                DefinitionModel* model = parser.releaseModel();
                recipeRenderer_.setModel(model, Definition::ownModel);
                break;
            }
            default:
                assert(false);
                break;
        }
    }
    update();
}


