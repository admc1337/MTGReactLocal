from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import base64
import json

import requests
import pandas as pd
import time
import re  # For regular expressions to parse mana costs
import matplotlib.pyplot as plt  # For plotting
import seaborn as sns  # Import seaborn
import numpy as np  # For numerical operations (e.g., filtering zeros for plot)

app = FastAPI(title="MTG Deck Analyzer", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API


class DecklistInput(BaseModel):
    decklist: str


class CardResponse(BaseModel):
    name: str
    color_identity: List[str]
    type_line: str
    cmc: float
    quantity: int


class DeckAnalysisResponse(BaseModel):
    cards: List[CardResponse]
    color_distribution: Dict[str, int]
    color_percentages: Dict[str, float]
    mana_curve: Dict[int, int]
    color_chart_base64: str
    mana_curve_chart_base64: str
    color_breakdown_chart_base64: str


def fetchData(cardname):
    """
    makes the api call to scryfall to get json data back
    """
    apiurl = "https://api.scryfall.com/cards/named"
    params = {"exact": cardname}

    try:
        response = requests.get(apiurl, params=params)
        response.raise_for_status()  # For error checking
        carddata = response.json()

        # Grabs all the data I want from the json file
        return {
            'name': carddata.get('name'),
            'color_identity': carddata.get('color_identity', []),
            'type_line': carddata.get('type_line'),
            'cmc': carddata.get('cmc')
        }
    # Returns error if failed (usually due to typo in card name)
    except requests.RequestException as error:
        print(f"Error fetching data for '{cardname}': {error}")
        return None


def analyzeDecklist(decklist_text):
    """
    Modified version of your original function to work with text input instead of file
    """
    cardData = []
    lines = decklist_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(r'(\d+)\s+(.*)', line)
        if match:
            quantity = int(match.group(1))
            cardName = match.group(2).strip()
        else:
            quantity = 1
            cardName = line.strip()

        print(f"Processing: {cardName} (x{quantity})")
        data = fetchData(cardName)
        if data:
            data['quantity'] = quantity
            cardData.append(data)
        else:
            print(f"Skipping '{cardName} due to fetch error or not found")
        time.sleep(0.05)  # Scryfall asks to rate limit
    return cardData


def countColorIdentity(dataFrame):
    """
    Counts total color identity of the deck
    """
    colorCounts = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}

    for index, row in dataFrame.iterrows():
        quantity = row['quantity']
        identity = row['color_identity']

        if not identity:
            if not (row['type_line'] and "Land" in row['type_line']):
                colorCounts['C'] += quantity
        else:
            for color in identity:
                if color in colorCounts:
                    colorCounts[color] += quantity
                else:
                    print(f"Warning: Unexpected color identity '{color}'")
    return colorCounts


def create_color_pie_chart_base64(filteredIDCount):
    """
    Creates color pie chart but returns base64 string
    """
    if not filteredIDCount:
        return ""

    labels = filteredIDCount.keys()
    sizes = filteredIDCount.values()

    colorMap = {
        'W': '#F9FAF9', 'U': '#ADD8E6', 'B': '#36454F', 'R': '#DC143C', 'G': '#7CFC00',
        'C': '#A9A9A9'
    }

    plotColors = [colorMap.get(label, '#CCCCCC') for label in labels]

    plt.figure(figsize=(10, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=plotColors,
            wedgeprops={'edgecolor': 'black', 'linewidth': 0.5},
            textprops={'fontsize': 12})
    plt.title(
        'Deck Color Identity Distribution (Per Nonland Card)', fontsize=16)
    plt.axis('equal')

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64


def create_mana_curve_chart_base64(cmcIntDict):
    """
    Creates your original mana curve chart but returns base64 string
    """
    if not cmcIntDict:
        return ""

    # Creates new Panda frame from cmcintdict
    manaCurveData = pd.DataFrame(
        list(cmcIntDict.items()), columns=['CMC', 'Count'])
    manaCurveData['CMC'] = pd.Categorical(manaCurveData['CMC'],
                                          categories=sorted(
                                              manaCurveData['CMC'].unique()),
                                          ordered=True)
    manaCurveData = manaCurveData.sort_values('CMC')

    plt.figure(figsize=(12, 6))
    sns.barplot(x='CMC', y='Count', data=manaCurveData,
                palette='coolwarm', edgecolor='black')
    plt.title(
        'Mana Curve (Converted Mana Cost Distribution of Spells)', fontsize=16)
    plt.xlabel('Converted Mana Cost (CMC)', fontsize=14)
    plt.ylabel('Number of Spells', fontsize=14)
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)  # Added grid back
    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64


def create_color_breakdown_chart_base64(IDPercentage):
    """
    Creates your original color breakdown chart but returns base64 string
    """
    if not IDPercentage:
        return ""

    colorMap = {
        'W': '#F9FAF9', 'U': '#ADD8E6', 'B': '#36454F', 'R': '#DC143C', 'G': '#7CFC00',
        'C': '#A9A9A9'
    }

    IDPercentagedf = pd.DataFrame([IDPercentage])

    orderedCol = [c for c in ['W', 'U', 'B', 'R',
                              'G', 'C'] if c in IDPercentagedf.columns]
    IDPercentagedf = IDPercentagedf[orderedCol]

    currentPlotColors = [colorMap.get(
        col, '#CCCCCC') for col in IDPercentagedf.columns]

    plt.figure(figsize=(10, 4))  # Adjust figure size for a single bar
    # Plot as a stacked horizontal bar chart
    IDPercentagedf.plot(
        kind='barh',
        stacked=True,
        ax=plt.gca(),  # Get current axes to plot on
        color=currentPlotColors,
        edgecolor='black',
        linewidth=0.5
    )
    plt.title(
        'Color Identity Breakdown (Percentage of Total Identity)', fontsize=16)
    plt.xlabel('Percentage of Deck Color Identity', fontsize=14)
    plt.ylabel('')  # No y-label needed for a single stacked bar
    # Set x-ticks from 0-100 in steps of 10
    plt.xticks(np.arange(0, 101, 10))
    plt.xlim(0, 100)  # Ensure x-axis goes exactly from 0 to 100
    plt.legend(title='Color', bbox_to_anchor=(1.05, 1),
               loc='upper left')  # Move legend outside
    plt.tight_layout()

    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64

    # API Routes


@app.get("/")
async def root():
    return {"message": "MTG Deck Analyzer API"}


@app.post("/analyze-deck", response_model=DeckAnalysisResponse)
async def analyze_deck(deck_input: DecklistInput):
    """
    API endpoint that uses your original analysis logic
    """
    try:
        # Use your original analyzeDecklist function (modified for text input)
        allCardData = analyzeDecklist(deck_input.decklist)

        if not allCardData:
            raise HTTPException(
                status_code=400, detail="No valid cards found in decklist")

        df = pd.DataFrame(allCardData)

        if 'quantity' not in df.columns:
            print(f"Warning: 'quantity' not found in DataFrame, making all quantities 1")
            df['quantity'] = 1

        # splits the dataframe into two separate copies (your original logic)
        nonlandDf = df[~df['type_line'].str.contains('Land',
                                                     na=False)].copy()

        landDf = df[df['type_line'].str.contains('Land',
                                                 na=False)].copy()

        # Getting color identity based on all nonland cards (your original logic)
        deckColorIDCount = countColorIdentity(nonlandDf)
        filteredIDCount = {
            k: v for k, v in deckColorIDCount.items() if v > 0}

        # Calculates percentages of each color from nonland cards (your original logic)
        totalIDPoints = sum(filteredIDCount.values())
        IDPercentage = {}
        if totalIDPoints > 0:
            IDPercentage = {
                k: (v / totalIDPoints) * 100 for k, v in filteredIDCount.items()}

        # Getting CMC per group in decklist (your original logic)
        # Learning Pandas functionality
        cmcDataSeries = nonlandDf.groupby('cmc')['quantity'].sum()
        cmcDict = cmcDataSeries.to_dict()
        # Convert keys to int for plotting and readablity
        cmcIntDict = {int(k): v for k, v in cmcDict.items()}

        # Generate charts using your original styling
        sns.set_theme(style="darkgrid", palette="pastel")

        color_chart_base64 = create_color_pie_chart_base64(filteredIDCount)
        mana_curve_chart_base64 = create_mana_curve_chart_base64(cmcIntDict)
        color_breakdown_chart_base64 = create_color_breakdown_chart_base64(
            IDPercentage)

        # Convert card data to response format
        cards = [CardResponse(**card) for card in allCardData]

        return DeckAnalysisResponse(
            cards=cards,
            color_distribution=filteredIDCount,
            color_percentages=IDPercentage,
            mana_curve=cmcIntDict,
            color_chart_base64=color_chart_base64,
            mana_curve_chart_base64=mana_curve_chart_base64,
            color_breakdown_chart_base64=color_breakdown_chart_base64
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing deck: {str(e)}")


@app.post("/upload-decklist")
async def upload_decklist(file: UploadFile = File(...)):
    """Upload a decklist file and return analysis"""
    try:
        content = await file.read()
        decklist_text = content.decode('utf-8')

        deck_input = DecklistInput(decklist=decklist_text)
        return await analyze_deck(deck_input)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
