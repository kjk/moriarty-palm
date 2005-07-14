#include <DefinitionStyle.hpp>
#include <Graphics.hpp>
#include <Text.hpp>
#include <Logging.hpp>

#include "MoriartyStyles.hpp"

StaticAssert<COLOR_NOT_DEF_INDEX != COLOR_DEF_INDEX>;

// keep this array sorted!
static const StaticStyleEntry staticStyleTable[] =
{
    //do not touch .xxx styles (keep them 
    {styleNameDefault, {BLACK, WHITE, stdFont, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, noUnderline}},
    {styleNameHyperlink, {COLOR_UI_FORM_FRAME, COLOR_NOT_DEF, FONT_NOT_DEF, NOT_DEF, NOT_DEF, NOT_DEF, NOT_DEF, NOT_DEF, NOT_DEF, grayUnderline}},

    COLOR(styleNameBlack,BLACK),
    COLOR(styleNameBlue,BLUE),
    COLOR_BOLD(styleNameBold,COLOR_NOT_DEF),
    COLOR_BOLD(styleNameBoldBlue,BLUE),
    COLOR_BOLD(styleNameBoldGreen,GREEN),
    COLOR_BOLD(styleNameBoldRed,RED),
    COLOR(styleNameGray,GRAY),
    COLOR(styleNameGreen,GREEN),
    COLOR_BOLD(styleNameHeader, COLOR_UI_FORM_FRAME),
    COLOR_AND_FONT(styleNameLarge, COLOR_NOT_DEF, largeFont),
    COLOR_AND_FONT(styleNameLargeBlue, BLUE, largeFont),
    COLOR_AND_FONT_BOLD(styleNamePageTitle, COLOR_UI_MENU_SELECTED_FILL, largeFont),
    COLOR(styleNameRed,RED),
    COLOR_AND_FONT(styleNameSmallGray, GRAY, smallFont),
    COLOR(styleNameSmallHeader, COLOR_UI_FORM_FRAME),
    COLOR_BOLD(styleNameStockPriceDown, RED),
    COLOR_BOLD(styleNameStockPriceUp, GREEN),
    COLOR(styleNameYellow,YELLOW)
};


uint_t StyleGetStaticStyleCount()
{
    return ARRAY_SIZE(staticStyleTable);
}

const char* StyleGetStaticStyleName(uint_t index)
{
    assert(index < ARRAY_SIZE(staticStyleTable));
    return staticStyleTable[index].name;
}

const DefinitionStyle* StyleGetStaticStyle(uint_t index)
{
    assert(index < ARRAY_SIZE(staticStyleTable));
    return &staticStyleTable[index].style;
}

const DefinitionStyle* StyleGetStaticStyle(const char* name, uint_t length)
{
    return StyleGetStaticStyleHelper(staticStyleTable, ARRAY_SIZE(staticStyleTable), name, length);
}

void StylePrepareStaticStyles()
{
}

void StyleDisposeStaticStyles()
{
}

#ifndef NDEBUG

void test_StaticStyleTable()
{
    // Validate that fields_ are sorted.
    for (uint_t i = 0; i < ARRAY_SIZE(staticStyleTable); ++i)
    {
        if (i > 0 && staticStyleTable[i] < staticStyleTable[i-1])
        {
            const char_t* prevName = staticStyleTable[i-1].name;
            const char_t* nextName = staticStyleTable[i].name;
            assert(false);
        }
    }
    
    //test |= operator on NULL style
    DefinitionStyle* ptr = NULL;
    DefinitionStyle s = *StyleGetStaticStyle(styleIndexDefault);
    s |= *ptr;
}

#endif

