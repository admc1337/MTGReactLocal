import React, { useState } from 'react';
import { Upload, BarChart3, PieChart, TrendingUp, FileText, Loader2 } from 'lucide-react';

const MTGDeckAnalyzer = () => {
  const [decklist, setDecklist] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('input');

  const analyzeDecklist = async () => {
    if (!decklist.trim()) {
      setError('Please enter a decklist');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/analyze-deck', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ decklist }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to analyze deck');
      }

      const data = await response.json();
      setAnalysis(data);
      setActiveTab('results');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/upload-decklist', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload file');
      }

      const data = await response.json();
      setAnalysis(data);
      setActiveTab('results');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sampleDecklist = `4 Lightning Bolt
4 Counterspell
2 Jace, the Mind Sculptor
4 Snapcaster Mage
3 Force of Will
4 Brainstorm
2 Cryptic Command
4 Scalding Tarn
4 Flooded Strand
4 Island
3 Mountain
2 Steam Vents
1 Sulfur Falls`;

  const ColorIcon = ({ color }) => {
    const colorStyles = {
      W: 'bg-gray-800 text-yellow-400 border-yellow-400/60 shadow-yellow-400/20',
      U: 'bg-gray-800 text-blue-400 border-blue-400/60 shadow-blue-400/20',
      B: 'bg-gray-900 text-gray-300 border-gray-400/60 shadow-gray-400/20',
      R: 'bg-gray-800 text-red-400 border-red-400/60 shadow-red-400/20',
      G: 'bg-gray-800 text-green-400 border-green-400/60 shadow-green-400/20',
      C: 'bg-gray-800 text-gray-400 border-gray-400/60 shadow-gray-400/20',
    };

    const colorNames = {
      W: 'White',
      U: 'Blue',
      B: 'Black',
      R: 'Red',
      G: 'Green',
      C: 'Colorless',
    };

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium border shadow-sm ${
          colorStyles[color] || 'bg-gray-800 text-gray-400 border-gray-400/60'
        }`}
      >
        {colorNames[color] || color}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Matrix-style animated background */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900/20 via-black to-gray-800/20"></div>
      
      <div className="relative w-full px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-green-400 mb-2 flex items-center justify-center gap-3 tracking-wide">
            <BarChart3 className="h-12 w-12 text-green-500" />
            MTG DECK ANALYZER
          </h1>
          <p className="text-green-300/80 text-lg font-mono">
            Analyze your Magic: The Gathering deck's color distribution and mana curve
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/50 p-1 shadow-lg shadow-green-500/20">
            <button
              onClick={() => setActiveTab('input')}
              className={`px-6 py-2 rounded font-medium transition-all duration-300 ${
                activeTab === 'input'
                  ? 'bg-green-500 text-black shadow-lg shadow-green-500/30'
                  : 'text-green-400 hover:bg-green-500/20 hover:text-green-300'
              }`}
            >
              <FileText className="inline h-4 w-4 mr-2" />
              INPUT DECK
            </button>
            <button
              onClick={() => setActiveTab('results')}
              disabled={!analysis}
              className={`px-6 py-2 rounded font-medium transition-all duration-300 ${
                activeTab === 'results' && analysis
                  ? 'bg-green-500 text-black shadow-lg shadow-green-500/30'
                  : 'text-green-400/60 cursor-not-allowed'
              }`}
            >
              <TrendingUp className="inline h-4 w-4 mr-2" />
              RESULTS
            </button>
          </div>
        </div>

        {/* Input Tab */}
        {activeTab === 'input' && (
          <div className="w-full">
            <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-8 shadow-2xl shadow-green-500/10">
              <h2 className="text-2xl font-bold text-green-400 mb-6 flex items-center gap-2 font-mono">
                <FileText className="h-6 w-6" />
                ENTER YOUR DECKLIST
              </h2>

              {/* Sample Decklist Button */}
              <div className="mb-4">
                <button
                  onClick={() => setDecklist(sampleDecklist)}
                  className="text-sm text-green-400 hover:text-green-300 underline font-mono transition-colors duration-200"
                >
                  Load Sample Decklist
                </button>
              </div>

              {/* Textarea */}
              <textarea
                value={decklist}
                onChange={(e) => setDecklist(e.target.value)}
                placeholder="Enter your decklist here... (e.g., '4 Lightning Bolt' or just 'Lightning Bolt')"
                className="w-full h-64 p-4 bg-black/80 border-2 border-green-500/40 rounded text-green-300 placeholder-green-500/60 focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-green-400 resize-none font-mono text-sm shadow-inner shadow-green-500/10"
              />

              {/* File Upload */}
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-green-400 rounded border border-green-500/50 cursor-pointer transition-all duration-200 hover:border-green-400">
                    <Upload className="h-4 w-4" />
                    UPLOAD FILE
                    <input
                      type="file"
                      accept=".txt,.list"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                  <span className="text-green-400/60 text-sm font-mono">or upload a .txt file</span>
                </div>

                <button
                  onClick={analyzeDecklist}
                  disabled={loading || !decklist.trim()}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-black disabled:text-gray-500 rounded font-medium transition-all duration-200 shadow-lg shadow-green-600/30 hover:shadow-green-500/40"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      ANALYZING...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="h-4 w-4" />
                      ANALYZE DECK
                    </>
                  )}
                </button>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mt-4 p-4 bg-red-900/30 border border-red-500/50 rounded text-red-400 font-mono text-sm">
                  ERROR: {error}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && analysis && (
          <div className="w-full space-y-8">
            {/* Deck Overview */}
            <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-6 shadow-2xl shadow-green-500/10">
              <h2 className="text-2xl font-bold text-green-400 mb-4 flex items-center gap-2 font-mono">
                <PieChart className="h-6 w-6" />
                DECK OVERVIEW
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 font-mono">{analysis.cards.length}</div>
                  <div className="text-green-300/80 font-mono text-sm">TOTAL CARDS</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 font-mono">
                    {Object.keys(analysis.color_distribution).length}
                  </div>
                  <div className="text-green-300/80 font-mono text-sm">COLORS</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 font-mono">
                    {Math.max(...Object.keys(analysis.mana_curve).map(Number))}
                  </div>
                  <div className="text-green-300/80 font-mono text-sm">MAX CMC</div>
                </div>
              </div>

              {/* Color Identity */}
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-green-400 mb-3 font-mono">COLOR IDENTITY</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(analysis.color_distribution).map(([color, count]) => (
                    <div key={color} className="flex items-center gap-2">
                      <ColorIcon color={color} />
                      <span className="text-green-300 font-medium font-mono">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Color Distribution Chart */}
              {analysis.color_chart_base64 && (
                <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-6 shadow-2xl shadow-green-500/10">
                  <h3 className="text-xl font-bold text-green-400 mb-4 font-mono">COLOR DISTRIBUTION</h3>
                  <div className="flex justify-center">
                    <img
                      src={`data:image/png;base64,${analysis.color_chart_base64}`}
                      alt="Color Distribution Chart"
                      className="max-w-full h-auto rounded border border-green-500/30"
                    />
                  </div>
                </div>
              )}

              {/* Mana Curve Chart */}
              {analysis.mana_curve_chart_base64 && (
                <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-6 shadow-2xl shadow-green-500/10">
                  <h3 className="text-xl font-bold text-green-400 mb-4 font-mono">MANA CURVE</h3>
                  <div className="flex justify-center">
                    <img
                      src={`data:image/png;base64,${analysis.mana_curve_chart_base64}`}
                      alt="Mana Curve Chart"
                      className="max-w-full h-auto rounded border border-green-500/30"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Color Breakdown Chart */}
            {analysis.color_breakdown_chart_base64 && (
              <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-6 shadow-2xl shadow-green-500/10">
                <h3 className="text-xl font-bold text-green-400 mb-4 font-mono">COLOR BREAKDOWN PERCENTAGE</h3>
                <div className="flex justify-center">
                  <img
                    src={`data:image/png;base64,${analysis.color_breakdown_chart_base64}`}
                    alt="Color Breakdown Chart"
                    className="max-w-full h-auto rounded border border-green-500/30"
                  />
                </div>
              </div>
            )}

            {/* Card List */}
            <div className="bg-gray-900/90 backdrop-blur-sm rounded border-2 border-green-500/60 p-6 shadow-2xl shadow-green-500/10">
              <h3 className="text-xl font-bold text-green-400 mb-4 font-mono">CARD LIST</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                {analysis.cards.map((card, index) => (
                  <div
                    key={index}
                    className="bg-black/60 rounded border border-green-500/30 p-3 hover:border-green-400/60 transition-colors duration-200"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-green-300 text-sm">{card.name}</span>
                      <span className="text-green-400 font-bold text-sm font-mono">×{card.quantity}</span>
                    </div>
                    <div className="text-xs text-green-400/70 mb-2 font-mono">{card.type_line}</div>
                    <div className="flex justify-between items-center">
                      <div className="flex gap-1">
                        {card.color_identity.map((color) => (
                          <ColorIcon key={color} color={color} />
                        ))}
                        {card.color_identity.length === 0 && <ColorIcon color="C" />}
                      </div>
                      <span className="text-green-400 font-medium text-sm font-mono">
                        CMC: {card.cmc}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MTGDeckAnalyzer;