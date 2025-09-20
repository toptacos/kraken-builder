<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class AnalysisController extends Controller
{
    private $flaskUrl;

    public function __construct()
    {
        $this->flaskUrl = env('FLASK_API_URL', 'http://localhost:8080');
    }

    /**
     * Get trading data from Flask API
     */
    public function getTradingData()
    {
        try {
            $response = Http::timeout(10)->get("{$this->flaskUrl}/status");

            if ($response->successful()) {
                $data = $response->json();
                return response()->json($data);
            }

            return response()->json(['error' => 'Failed to fetch trading data'], 500);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Get logs from Flask API
     */
    public function getLogs(Request $request)
    {
        try {
            $level = $request->get('level');
            $url = $level ? "{$this->flaskUrl}/logs/{$level}" : "{$this->flaskUrl}/logs";

            $response = Http::timeout(10)->get($url);

            if ($response->successful()) {
                $data = $response->json();
                return response()->json($data);
            }

            return response()->json(['error' => 'Failed to fetch logs'], 500);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Perform AI-powered technical analysis on trading data
     */
    public function technicalAnalysis(Request $request)
    {
        try {
            $symbol = $request->get('symbol', 'BTC/USDT');
            $timeframe = $request->get('timeframe', '1h');
            $period = $request->get('period', 50);
            $includeAltCoins = $request->get('include_alt_coins', true);

            // Get historical data from Flask API
            $response = Http::timeout(10)->get("{$this->flaskUrl}/historical-data", [
                'symbol' => $symbol,
                'timeframe' => $timeframe,
                'limit' => 200
            ]);

            if ($response->successful()) {
                $data = $response->json();
                $analysis = $this->performTechnicalAnalysis($data['data'] ?? [], $period);

                // Add AI-powered insights
                $aiInsights = $this->generateAIInsights($analysis, $symbol);

                // Include alt coin correlations if requested
                $altCoinAnalysis = [];
                if ($includeAltCoins) {
                    $altCoinAnalysis = $this->analyzeAltCoinCorrelations($symbol);
                }

                return response()->json([
                    'symbol' => $symbol,
                    'timeframe' => $timeframe,
                    'analysis' => $analysis,
                    'ai_insights' => $aiInsights,
                    'alt_coin_analysis' => $altCoinAnalysis,
                    'recommendations' => $this->generateRecommendations($analysis, $aiInsights),
                    'timestamp' => now()->toISOString()
                ]);
            }

            return response()->json(['error' => 'Failed to fetch historical data'], 500);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Perform statistical analysis
     */
    public function statisticalAnalysis(Request $request)
    {
        try {
            $data = $request->get('data', []);
            $analysis = $this->performStatisticalAnalysis($data);

            return response()->json([
                'analysis' => $analysis,
                'timestamp' => now()->toISOString()
            ]);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Get performance metrics
     */
    public function performanceMetrics(Request $request)
    {
        try {
            $startDate = $request->get('start_date');
            $endDate = $request->get('end_date');

            // Get trading history from Flask API
            $response = Http::timeout(10)->get("{$this->flaskUrl}/trading-history", [
                'start_date' => $startDate,
                'end_date' => $endDate
            ]);

            if ($response->successful()) {
                $data = $response->json();
                $metrics = $this->calculatePerformanceMetrics($data['trades'] ?? []);

                return response()->json([
                    'metrics' => $metrics,
                    'period' => ['start' => $startDate, 'end' => $endDate],
                    'timestamp' => now()->toISOString()
                ]);
            }

            return response()->json(['error' => 'Failed to fetch trading history'], 500);
        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }

    /**
     * Perform technical analysis calculations
     */
    private function performTechnicalAnalysis($data, $period)
    {
        if (empty($data)) {
            return ['error' => 'No data available for analysis'];
        }

        $closes = array_column($data, 'close');
        $highs = array_column($data, 'high');
        $lows = array_column($data, 'low');

        return [
            'sma' => $this->calculateSMA($closes, $period),
            'ema' => $this->calculateEMA($closes, $period),
            'rsi' => $this->calculateRSI($closes, 14),
            'macd' => $this->calculateMACD($closes),
            'bollinger_bands' => $this->calculateBollingerBands($closes, 20),
            'stochastic' => $this->calculateStochastic($highs, $lows, $closes, 14),
            'williams_r' => $this->calculateWilliamsR($highs, $lows, $closes, 14),
            'trend_analysis' => $this->analyzeTrend($closes),
            'support_resistance' => $this->findSupportResistance($highs, $lows)
        ];
    }

    /**
     * Perform statistical analysis
     */
    private function performStatisticalAnalysis($data)
    {
        if (empty($data)) {
            return ['error' => 'No data available for analysis'];
        }

        $values = array_column($data, 'value') ?? $data;

        return [
            'mean' => $this->calculateMean($values),
            'median' => $this->calculateMedian($values),
            'mode' => $this->calculateMode($values),
            'standard_deviation' => $this->calculateStandardDeviation($values),
            'variance' => $this->calculateVariance($values),
            'skewness' => $this->calculateSkewness($values),
            'kurtosis' => $this->calculateKurtosis($values),
            'quartiles' => $this->calculateQuartiles($values),
            'correlation' => count($data) > 1 ? $this->calculateCorrelation($data) : null
        ];
    }

    /**
     * Calculate performance metrics
     */
    private function calculatePerformanceMetrics($trades)
    {
        if (empty($trades)) {
            return ['error' => 'No trades available for analysis'];
        }

        $totalTrades = count($trades);
        $winningTrades = count(array_filter($trades, fn($trade) => ($trade['profit'] ?? 0) > 0));
        $losingTrades = $totalTrades - $winningTrades;

        $profits = array_column($trades, 'profit');
        $totalProfit = array_sum($profits);
        $winRate = $totalTrades > 0 ? ($winningTrades / $totalTrades) * 100 : 0;

        return [
            'total_trades' => $totalTrades,
            'winning_trades' => $winningTrades,
            'losing_trades' => $losingTrades,
            'win_rate' => round($winRate, 2),
            'total_profit' => round($totalProfit, 2),
            'average_profit' => $totalTrades > 0 ? round($totalProfit / $totalTrades, 2) : 0,
            'largest_win' => !empty($profits) ? max($profits) : 0,
            'largest_loss' => !empty($profits) ? min($profits) : 0,
            'profit_factor' => $this->calculateProfitFactor($profits),
            'sharpe_ratio' => $this->calculateSharpeRatio($profits),
            'max_drawdown' => $this->calculateMaxDrawdown($profits)
        ];
    }

    // Technical Analysis Methods
    private function calculateSMA($data, $period)
    {
        $result = [];
        for ($i = $period - 1; $i < count($data); $i++) {
            $sum = 0;
            for ($j = $i - $period + 1; $j <= $i; $j++) {
                $sum += $data[$j];
            }
            $result[] = $sum / $period;
        }
        return $result;
    }

    private function calculateEMA($data, $period)
    {
        $multiplier = 2 / ($period + 1);
        $result = [$data[0]];

        for ($i = 1; $i < count($data); $i++) {
            $ema = ($data[$i] - $result[$i - 1]) * $multiplier + $result[$i - 1];
            $result[] = $ema;
        }
        return $result;
    }

    private function calculateRSI($data, $period)
    {
        $gains = [];
        $losses = [];

        for ($i = 1; $i < count($data); $i++) {
            $change = $data[$i] - $data[$i - 1];
            $gains[] = $change > 0 ? $change : 0;
            $losses[] = $change < 0 ? abs($change) : 0;
        }

        $avgGain = array_sum(array_slice($gains, 0, $period)) / $period;
        $avgLoss = array_sum(array_slice($losses, 0, $period)) / $period;

        for ($i = $period; $i < count($gains); $i++) {
            $avgGain = ($avgGain * ($period - 1) + $gains[$i]) / $period;
            $avgLoss = ($avgLoss * ($period - 1) + $losses[$i]) / $period;
        }

        $rs = $avgLoss != 0 ? $avgGain / $avgLoss : 0;
        return 100 - (100 / (1 + $rs));
    }

    private function calculateMACD($data)
    {
        $ema12 = $this->calculateEMA($data, 12);
        $ema26 = $this->calculateEMA($data, 26);

        $macd = [];
        for ($i = 0; $i < min(count($ema12), count($ema26)); $i++) {
            $macd[] = $ema12[$i] - $ema26[$i];
        }

        $signal = $this->calculateEMA($macd, 9);

        return [
            'macd' => $macd,
            'signal' => $signal,
            'histogram' => array_map(fn($a, $b) => $a - $b, $macd, $signal)
        ];
    }

    private function calculateBollingerBands($data, $period)
    {
        $sma = $this->calculateSMA($data, $period);

        $bands = [];
        for ($i = 0; $i < count($sma); $i++) {
            $slice = array_slice($data, $i, $period);
            $std = $this->calculateStandardDeviation($slice);
            $bands[] = [
                'upper' => $sma[$i] + (2 * $std),
                'middle' => $sma[$i],
                'lower' => $sma[$i] - (2 * $std)
            ];
        }
        return $bands;
    }

    private function calculateStochastic($highs, $lows, $closes, $period)
    {
        $k = [];
        for ($i = $period - 1; $i < count($closes); $i++) {
            $highest = max(array_slice($highs, $i - $period + 1, $period));
            $lowest = min(array_slice($lows, $i - $period + 1, $period));
            $k[] = $lowest != $highest ? (($closes[$i] - $lowest) / ($highest - $lowest)) * 100 : 0;
        }

        $d = $this->calculateSMA($k, 3);
        return ['k' => $k, 'd' => $d];
    }

    private function calculateWilliamsR($highs, $lows, $closes, $period)
    {
        $r = [];
        for ($i = $period - 1; $i < count($closes); $i++) {
            $highest = max(array_slice($highs, $i - $period + 1, $period));
            $lowest = min(array_slice($lows, $i - $period + 1, $period));
            $r[] = $highest != $lowest ? (($highest - $closes[$i]) / ($highest - $lowest)) * -100 : 0;
        }
        return $r;
    }

    private function analyzeTrend($data)
    {
        if (count($data) < 2) return 'insufficient_data';

        $slope = $this->calculateLinearRegressionSlope($data);
        $strength = abs($slope) / (array_sum($data) / count($data)) * 100;

        if ($slope > 0.001) return ['direction' => 'uptrend', 'strength' => $strength];
        if ($slope < -0.001) return ['direction' => 'downtrend', 'strength' => $strength];
        return ['direction' => 'sideways', 'strength' => $strength];
    }

    private function findSupportResistance($highs, $lows)
    {
        $support = min($lows);
        $resistance = max($highs);

        return [
            'support' => $support,
            'resistance' => $resistance,
            'pivot' => ($support + $resistance) / 2
        ];
    }

    // Statistical Analysis Methods
    private function calculateMean($data)
    {
        return array_sum($data) / count($data);
    }

    private function calculateMedian($data)
    {
        sort($data);
        $count = count($data);
        $middle = floor($count / 2);
        return $count % 2 ? $data[$middle] : ($data[$middle - 1] + $data[$middle]) / 2;
    }

    private function calculateMode($data)
    {
        $counts = array_count_values($data);
        arsort($counts);
        return key($counts);
    }

    private function calculateStandardDeviation($data)
    {
        $mean = $this->calculateMean($data);
        $variance = array_sum(array_map(fn($x) => pow($x - $mean, 2), $data)) / count($data);
        return sqrt($variance);
    }

    private function calculateVariance($data)
    {
        $mean = $this->calculateMean($data);
        return array_sum(array_map(fn($x) => pow($x - $mean, 2), $data)) / count($data);
    }

    private function calculateSkewness($data)
    {
        $mean = $this->calculateMean($data);
        $std = $this->calculateStandardDeviation($data);
        $n = count($data);

        $sum = array_sum(array_map(fn($x) => pow(($x - $mean) / $std, 3), $data));
        return $n > 2 ? ($sum * $n) / (($n - 1) * ($n - 2)) : 0;
    }

    private function calculateKurtosis($data)
    {
        $mean = $this->calculateMean($data);
        $std = $this->calculateStandardDeviation($data);
        $n = count($data);

        $sum = array_sum(array_map(fn($x) => pow(($x - $mean) / $std, 4), $data));
        return $n > 3 ? (($sum * $n * ($n + 1)) / (($n - 1) * ($n - 2) * ($n - 3))) - (3 * pow($n - 1, 2) / (($n - 2) * ($n - 3))) : 0;
    }

    private function calculateQuartiles($data)
    {
        sort($data);
        $count = count($data);

        return [
            'q1' => $data[floor($count * 0.25)],
            'q2' => $this->calculateMedian($data),
            'q3' => $data[floor($count * 0.75)]
        ];
    }

    private function calculateCorrelation($data)
    {
        if (count($data) < 2) return null;

        $x = array_column($data, 'x');
        $y = array_column($data, 'y');

        $n = count($x);
        $sumX = array_sum($x);
        $sumY = array_sum($y);
        $sumXY = array_sum(array_map(fn($a, $b) => $a * $b, $x, $y));
        $sumX2 = array_sum(array_map(fn($x) => $x * $x, $x));
        $sumY2 = array_sum(array_map(fn($y) => $y * $y, $y));

        $numerator = ($n * $sumXY) - ($sumX * $sumY);
        $denominator = sqrt((($n * $sumX2) - pow($sumX, 2)) * (($n * $sumY2) - pow($sumY, 2)));

        return $denominator != 0 ? $numerator / $denominator : 0;
    }

    private function calculateProfitFactor($profits)
    {
        $wins = array_filter($profits, fn($p) => $p > 0);
        $losses = array_filter($profits, fn($p) => $p < 0);

        $totalWins = array_sum($wins);
        $totalLosses = abs(array_sum($losses));

        return $totalLosses != 0 ? $totalWins / $totalLosses : ($totalWins > 0 ? INF : 0);
    }

    private function calculateSharpeRatio($profits)
    {
        if (empty($profits)) return 0;

        $meanReturn = $this->calculateMean($profits);
        $stdDev = $this->calculateStandardDeviation($profits);

        return $stdDev != 0 ? $meanReturn / $stdDev : 0;
    }

    private function calculateMaxDrawdown($profits)
    {
        $cumulative = [0];
        $runningTotal = 0;
        $peak = 0;
        $maxDrawdown = 0;

        foreach ($profits as $profit) {
            $runningTotal += $profit;
            $cumulative[] = $runningTotal;

            if ($runningTotal > $peak) {
                $peak = $runningTotal;
            }

            $drawdown = $peak - $runningTotal;
            if ($drawdown > $maxDrawdown) {
                $maxDrawdown = $drawdown;
            }
        }

        return $maxDrawdown;
    }

    private function calculateLinearRegressionSlope($data)
    {
        $n = count($data);
        $x = range(0, $n - 1);

        $sumX = array_sum($x);
        $sumY = array_sum($data);
        $sumXY = array_sum(array_map(fn($a, $b) => $a * $b, $x, $data));
        $sumX2 = array_sum(array_map(fn($x) => $x * $x, $x));

        return (($n * $sumXY) - ($sumX * $sumY)) / (($n * $sumX2) - pow($sumX, 2));
    }

    /**
     * Generate AI-powered insights based on technical analysis
     */
    private function generateAIInsights($analysis, $symbol)
    {
        $insights = [
            'market_sentiment' => 'neutral',
            'trend_strength' => 'moderate',
            'volatility_assessment' => 'normal',
            'key_levels' => [],
            'predictions' => [],
            'risk_assessment' => 'medium'
        ];

        // Analyze RSI
        if (isset($analysis['rsi'])) {
            if ($analysis['rsi'] < 30) {
                $insights['market_sentiment'] = 'oversold';
                $insights['predictions'][] = 'Potential bullish reversal in short term';
            } elseif ($analysis['rsi'] > 70) {
                $insights['market_sentiment'] = 'overbought';
                $insights['predictions'][] = 'Potential bearish reversal in short term';
            }
        }

        // Analyze trend
        if (isset($analysis['trend_analysis'])) {
            $trend = $analysis['trend_analysis'];
            $insights['trend_strength'] = $trend['strength'] > 0.7 ? 'strong' : ($trend['strength'] > 0.3 ? 'moderate' : 'weak');

            if ($trend['direction'] === 'uptrend' && $trend['strength'] > 0.5) {
                $insights['predictions'][] = 'Strong upward momentum detected';
            }
        }

        // Analyze MACD
        if (isset($analysis['macd'])) {
            $macd = $analysis['macd'];
            $latestMacd = end($macd['macd']);
            $latestSignal = end($macd['signal']);

            if ($latestMacd > $latestSignal) {
                $insights['predictions'][] = 'MACD indicates bullish momentum';
            } else {
                $insights['predictions'][] = 'MACD indicates bearish momentum';
            }
        }

        // Volatility assessment
        if (isset($analysis['bollinger_bands'])) {
            $bands = end($analysis['bollinger_bands']);
            $price = $analysis['sma'] ? end($analysis['sma']) : 0;

            if ($price > $bands['upper']) {
                $insights['volatility_assessment'] = 'high';
                $insights['predictions'][] = 'Price above upper Bollinger Band - potential reversal';
            } elseif ($price < $bands['lower']) {
                $insights['volatility_assessment'] = 'high';
                $insights['predictions'][] = 'Price below lower Bollinger Band - potential bounce';
            }
        }

        // Risk assessment
        $riskFactors = 0;
        if ($insights['volatility_assessment'] === 'high') $riskFactors++;
        if ($insights['market_sentiment'] === 'overbought' || $insights['market_sentiment'] === 'oversold') $riskFactors++;
        if ($insights['trend_strength'] === 'weak') $riskFactors++;

        $insights['risk_assessment'] = $riskFactors >= 2 ? 'high' : ($riskFactors === 1 ? 'medium' : 'low');

        return $insights;
    }

    /**
     * Analyze correlations with alt coins
     */
    private function analyzeAltCoinCorrelations($baseSymbol)
    {
        $altCoins = [
            'ETH/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'LINK/USDT',
            'AVAX/USDT', 'MATIC/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT'
        ];

        $correlations = [];

        try {
            // Get base symbol data
            $baseResponse = Http::timeout(10)->get("{$this->flaskUrl}/historical-data", [
                'symbol' => $baseSymbol,
                'timeframe' => '1d',
                'limit' => 30
            ]);

            if ($baseResponse->successful()) {
                $baseData = $baseResponse->json()['data'] ?? [];
                $basePrices = array_column($baseData, 'close');

                foreach ($altCoins as $altCoin) {
                    try {
                        $altResponse = Http::timeout(5)->get("{$this->flaskUrl}/historical-data", [
                            'symbol' => $altCoin,
                            'timeframe' => '1d',
                            'limit' => 30
                        ]);

                        if ($altResponse->successful()) {
                            $altData = $altResponse->json()['data'] ?? [];
                            $altPrices = array_column($altData, 'close');

                            if (count($basePrices) === count($altPrices)) {
                                $correlation = $this->calculateCorrelation([
                                    ['x' => $basePrices, 'y' => $altPrices]
                                ]);

                                $correlations[] = [
                                    'symbol' => $altCoin,
                                    'correlation' => round($correlation, 4),
                                    'strength' => abs($correlation) > 0.7 ? 'strong' :
                                                 (abs($correlation) > 0.3 ? 'moderate' : 'weak'),
                                    'direction' => $correlation > 0 ? 'positive' : 'negative'
                                ];
                            }
                        }
                    } catch (\Exception $e) {
                        // Skip failed alt coin analysis
                        continue;
                    }
                }

                // Sort by correlation strength
                usort($correlations, fn($a, $b) => abs($b['correlation']) <=> abs($a['correlation']));
            }
        } catch (\Exception $e) {
            // Return empty correlations if analysis fails
        }

        return array_slice($correlations, 0, 5); // Return top 5 correlations
    }

    /**
     * Generate trading recommendations based on analysis
     */
    private function generateRecommendations($analysis, $aiInsights)
    {
        $recommendations = [
            'primary_action' => 'hold',
            'confidence' => 0,
            'timeframe' => 'short_term',
            'risk_level' => 'medium',
            'reasoning' => [],
            'alternatives' => []
        ];

        $score = 0;
        $reasons = [];

        // RSI-based recommendations
        if (isset($analysis['rsi'])) {
            if ($analysis['rsi'] < 30) {
                $score += 20;
                $reasons[] = 'RSI indicates oversold conditions - potential buying opportunity';
            } elseif ($analysis['rsi'] > 70) {
                $score -= 20;
                $reasons[] = 'RSI indicates overbought conditions - potential selling opportunity';
            }
        }

        // Trend-based recommendations
        if (isset($analysis['trend_analysis'])) {
            $trend = $analysis['trend_analysis'];
            if ($trend['direction'] === 'uptrend' && $trend['strength'] > 0.5) {
                $score += 15;
                $reasons[] = 'Strong uptrend detected - favorable for long positions';
            } elseif ($trend['direction'] === 'downtrend' && $trend['strength'] > 0.5) {
                $score -= 15;
                $reasons[] = 'Strong downtrend detected - consider short positions or staying out';
            }
        }

        // MACD-based recommendations
        if (isset($analysis['macd'])) {
            $macd = $analysis['macd'];
            $latestMacd = end($macd['macd']);
            $latestSignal = end($macd['signal']);

            if ($latestMacd > $latestSignal) {
                $score += 10;
                $reasons[] = 'MACD shows bullish momentum';
            } else {
                $score -= 10;
                $reasons[] = 'MACD shows bearish momentum';
            }
        }

        // Bollinger Bands recommendations
        if (isset($analysis['bollinger_bands'])) {
            $bands = end($analysis['bollinger_bands']);
            $price = $analysis['sma'] ? end($analysis['sma']) : 0;

            if ($price < $bands['lower']) {
                $score += 12;
                $reasons[] = 'Price near lower Bollinger Band - potential mean reversion';
            } elseif ($price > $bands['upper']) {
                $score -= 12;
                $reasons[] = 'Price near upper Bollinger Band - potential reversal';
            }
        }

        // AI insights integration
        if ($aiInsights['market_sentiment'] === 'oversold') {
            $score += 8;
            $reasons[] = 'AI analysis detects oversold market conditions';
        } elseif ($aiInsights['market_sentiment'] === 'overbought') {
            $score -= 8;
            $reasons[] = 'AI analysis detects overbought market conditions';
        }

        // Determine primary action
        if ($score >= 25) {
            $recommendations['primary_action'] = 'buy';
            $recommendations['confidence'] = min(95, 50 + $score);
        } elseif ($score <= -25) {
            $recommendations['primary_action'] = 'sell';
            $recommendations['confidence'] = min(95, 50 + abs($score));
        } else {
            $recommendations['primary_action'] = 'hold';
            $recommendations['confidence'] = max(20, 50 - abs($score));
        }

        // Risk assessment
        if ($aiInsights['risk_assessment'] === 'high') {
            $recommendations['risk_level'] = 'high';
            $recommendations['reasoning'][] = 'High risk conditions detected - reduce position sizes';
        } elseif ($aiInsights['risk_assessment'] === 'low') {
            $recommendations['risk_level'] = 'low';
            $recommendations['reasoning'][] = 'Low risk conditions - normal position sizes acceptable';
        }

        $recommendations['reasoning'] = array_merge($recommendations['reasoning'], $reasons);

        // Generate alternatives
        if ($recommendations['primary_action'] === 'buy') {
            $recommendations['alternatives'] = ['hold', 'wait'];
        } elseif ($recommendations['primary_action'] === 'sell') {
            $recommendations['alternatives'] = ['hold', 'short'];
        } else {
            $recommendations['alternatives'] = ['buy', 'sell'];
        }

        return $recommendations;
    }
}