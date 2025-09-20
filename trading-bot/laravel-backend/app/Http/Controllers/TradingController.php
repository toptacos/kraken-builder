<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\TradeLog;
use App\Models\TradingSession;

class TradingController extends Controller
{
    protected $flaskUrl;

    public function __construct()
    {
        $this->flaskUrl = env('FLASK_API_URL', 'http://trading-bot:8080');
    }

    /**
     * Get trading dashboard data
     */
    public function dashboard()
    {
        try {
            // Get data from Flask API
            $healthResponse = Http::timeout(5)->get("{$this->flaskUrl}/health");
            $statusResponse = Http::timeout(5)->get("{$this->flaskUrl}/status");
            $logsResponse = Http::timeout(5)->get("{$this->flaskUrl}/logs");

            $health = $healthResponse->successful() ? $healthResponse->json() : null;
            $status = $statusResponse->successful() ? $statusResponse->json() : null;
            $logs = $logsResponse->successful() ? $logsResponse->json() : null;

            // Get recent trades from database
            $recentTrades = TradeLog::latest()->take(10)->get();
            $currentSession = TradingSession::where('status', 'active')->first();

            return response()->json([
                'success' => true,
                'data' => [
                    'health' => $health,
                    'status' => $status,
                    'logs' => $logs,
                    'recent_trades' => $recentTrades,
                    'current_session' => $currentSession,
                    'timestamp' => now()->toISOString()
                ]
            ]);

        } catch (\Exception $e) {
            Log::error('Dashboard data fetch failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Failed to fetch dashboard data',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get trading logs with filtering
     */
    public function logs(Request $request)
    {
        try {
            $level = $request->get('level');
            $limit = $request->get('limit', 100);

            if ($level) {
                // Get filtered logs from Flask API
                $response = Http::timeout(5)->get("{$this->flaskUrl}/logs/{$level}");
            } else {
                // Get all logs from Flask API
                $response = Http::timeout(5)->get("{$this->flaskUrl}/logs");
            }

            $logs = $response->successful() ? $response->json() : ['logs' => []];

            // Store logs in database for persistence
            if (isset($logs['logs']) && is_array($logs['logs'])) {
                foreach (array_slice($logs['logs'], 0, 10) as $log) {
                    TradeLog::create([
                        'level' => $log['level'] ?? 'INFO',
                        'message' => $log['message'] ?? '',
                        'timestamp' => isset($log['timestamp']) ? $log['timestamp'] : now(),
                        'source' => 'flask_api'
                    ]);
                }
            }

            return response()->json([
                'success' => true,
                'data' => $logs
            ]);

        } catch (\Exception $e) {
            Log::error('Logs fetch failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Failed to fetch logs',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Execute a test trade
     */
    public function testTrade()
    {
        try {
            $response = Http::timeout(10)->get("{$this->flaskUrl}/test_trade");

            if ($response->successful()) {
                $result = $response->json();

                // Log the test trade
                TradeLog::create([
                    'level' => 'INFO',
                    'message' => 'Test trade executed: ' . ($result['message'] ?? 'Unknown result'),
                    'timestamp' => now(),
                    'source' => 'test_trade'
                ]);

                return response()->json([
                    'success' => true,
                    'data' => $result
                ]);
            }

            return response()->json([
                'success' => false,
                'error' => 'Test trade failed'
            ], 500);

        } catch (\Exception $e) {
            Log::error('Test trade failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Test trade execution failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Run trading cycle
     */
    public function runCycle()
    {
        try {
            $response = Http::timeout(30)->get("{$this->flaskUrl}/run_cycle");

            if ($response->successful()) {
                $result = $response->json();

                // Log the cycle execution
                TradeLog::create([
                    'level' => 'INFO',
                    'message' => 'Trading cycle executed: ' . ($result['message'] ?? 'Completed'),
                    'timestamp' => now(),
                    'source' => 'trading_cycle'
                ]);

                return response()->json([
                    'success' => true,
                    'data' => $result
                ]);
            }

            return response()->json([
                'success' => false,
                'error' => 'Trading cycle failed'
            ], 500);

        } catch (\Exception $e) {
            Log::error('Trading cycle failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Trading cycle execution failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get trading statistics
     */
    public function statistics()
    {
        try {
            $totalTrades = TradeLog::where('source', 'trading_cycle')->count();
            $profitableTrades = TradeLog::where('message', 'like', '%PROFITABLE%')->count();
            $winRate = $totalTrades > 0 ? ($profitableTrades / $totalTrades) * 100 : 0;

            $recentTrades = TradeLog::where('source', 'trading_cycle')
                ->latest()
                ->take(50)
                ->get();

            $totalProfit = 0;
            foreach ($recentTrades as $trade) {
                if (preg_match('/[\+\-]\$([\d\.]+)/', $trade->message, $matches)) {
                    $amount = floatval($matches[1]);
                    $totalProfit += strpos($trade->message, '+') !== false ? $amount : -$amount;
                }
            }

            return response()->json([
                'success' => true,
                'data' => [
                    'total_trades' => $totalTrades,
                    'profitable_trades' => $profitableTrades,
                    'win_rate' => round($winRate, 2),
                    'total_profit' => round($totalProfit, 2),
                    'recent_trades' => $recentTrades
                ]
            ]);

        } catch (\Exception $e) {
            Log::error('Statistics fetch failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Failed to fetch statistics',
                'message' => $e->getMessage()
            ], 500);
        }
    }
}