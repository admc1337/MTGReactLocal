from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import base64
import json
import os

import requests
import pandas as pd
import time
import re
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Vercel
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

app = FastAPI(title="MTG Deck Analyzer", version="1.0.0")

# Add CORS middleware - allow all origins for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
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
        response = requests.get(apiurl, params=params, timeout=10)
        response.raise_for_status()
        carddata = response.json()

        return {
            'name': carddata.get('name'),
            'color_identity': carddata.get('color_identity', []),
            'type_line': carddata.get('type_line'),
            'cmc': carddata.get('cmc')
        }
    except requests.RequestException as error:
        print(f"Error fetching data for '{cardname}': {error}")
        return None

def analyzeDecklist(decklist_text):
    """
    Modified version to work with text input
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
            print(f"Skipping '{cardName}' due to fetch error or not found")
        time.sleep(0.1)  # Rate limiting for Scryfall API
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
    plt.title('Deck Color Identity Distribution (Per Nonland Card)', fontsize=16)
    plt.axis('equal')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64

def create_mana_curve_chart_base64(cmcIntDict):
    """
    Creates mana curve chart and returns base64 string
    """
    if not cmcIntDict:
        return ""

    manaCurveData = pd.DataFrame(
        list(cmcIntDict.items()), columns=['CMC', 'Count'])
    manaCurveData['CMC'] = pd.Categorical(manaCurveData['CMC'],
                                          categories=sorted(manaCurveData['CMC'].unique()),
                                          ordered=True)
    manaCurveData = manaCurveData.sort_values('CMC')

    plt.figure(figsize=(12, 6))
    sns.barplot(x='CMC', y='Count', data=manaCurveData,
                palette='coolwarm', edgecolor='black')
    plt.title('Mana Curve (Converted Mana Cost Distribution of Spells)', fontsize=16)
    plt.xlabel('Converted Mana Cost (CMC)', fontsize=14)
    plt.ylabel('Number of Spells', fontsize=14)
    plt.xticks(rotation=0)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64

def create_color_breakdown_chart_base64(IDPercentage):
    """
    Creates color breakdown chart and returns base64 string
    """
    if not IDPercentage:
        return ""

    colorMap = {
        'W': '#F9FAF9', 'U': '#ADD8E6', 'B': '#36454F', 'R': '#DC143C', 'G': '#7CFC00',
        'C': '#A9A9A9'
    }

    IDPercentagedf = pd.DataFrame([IDPercentage])
    orderedCol = [c for c in ['W', 'U', 'B', 'R', 'G', 'C'] if c in IDPercentagedf.columns]
    IDPercentagedf = IDPercentagedf[orderedCol]
    currentPlotColors = [colorMap.get(col, '#CCCCCC') for col in IDPercentagedf.columns]

    plt.figure(figsize=(10, 4))
    IDPercentagedf.plot(
        kind='barh',
        stacked=True,
        ax=plt.gca(),
        color=currentPlotColors,
        edgecolor='black',
        linewidth=0.5
    )
    plt.title('Color Identity Breakdown (Percentage of Total Identity)', fontsize=16)
    plt.xlabel('Percentage of Deck Color Identity', fontsize=14)
    plt.ylabel('')
    plt.xticks(np.arange(0, 101, 10))
    plt.xlim(0, 100)
    plt.legend(title='Color', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
    buffer.seek(0)
    imageBase64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return imageBase64

# API Routes
@app.get("/")
@app.get("/api")
async def root():
    return {"message": "MTG Deck Analyzer API"}

@app.post("/api/analyze-deck", response_model=DeckAnalysisResponse)
async def analyze_deck(deck_input: DecklistInput):
    """
    API endpoint that analyzes the deck
    """
    try:
        allCardData = analyzeDecklist(deck_input.decklist)

        if not allCardData:
            raise HTTPException(status_code=400, detail="No valid cards found in decklist")

        df = pd.DataFrame(allCardData)

        if 'quantity' not in df.columns:
            print(f"Warning: 'quantity' not found in DataFrame, making all quantities 1")
            df['quantity'] = 1

        nonlandDf = df[~df['type_line'].str.contains('Land', na=False)].copy()
        landDf = df[df['type_line'].str.contains('Land', na=False)].copy()

        deckColorIDCount = countColorIdentity(nonlandDf)
        filteredIDCount = {k: v for k, v in deckColorIDCount.items() if v > 0}

        totalIDPoints = sum(filteredIDCount.values())
        IDPercentage = {}
        if totalIDPoints > 0:
            IDPercentage = {k: (v / totalIDPoints) * 100 for k, v in filteredIDCount.items()}

        cmcDataSeries = nonlandDf.groupby('cmc')['quantity'].sum()
        cmcDict = cmcDataSeries.to_dict()
        cmcIntDict = {int(k): v for k, v in cmcDict.items()}

        # Set theme for charts
        sns.set_theme(style="darkgrid", palette="pastel")

        color_chart_base64 = create_color_pie_chart_base64(filteredIDCount)
        mana_curve_chart_base64 = create_mana_curve_chart_base64(cmcIntDict)
        color_breakdown_chart_base64 = create_color_breakdown_chart_base64(IDPercentage)

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
        raise HTTPException(status_code=500, detail=f"Error analyzing deck: {str(e)}")

@app.post("/api/upload-decklist")
async def upload_decklist(file: UploadFile = File(...)):
    """Upload a decklist file and return analysis"""
    try:
        content = await file.read()
        decklist_text = content.decode('utf-8')
        deck_input = DecklistInput(decklist=decklist_text)
        return await analyze_deck(deck_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# For Vercel serverless functions
def handler(request):
    return app