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
     * Get verified balance information with conservative limits
     */
    public function verifiedBalance()
    {
        try {
            // Get balance info from Flask API
            $response = Http::timeout(10)->get("{$this->flaskUrl}/verified-balance");

            if ($response->successful()) {
                $balanceData = $response->json();

                // Log balance verification
                TradeLog::create([
                    'level' => 'INFO',
                    'message' => 'Balance verification requested - Total verified: $' . ($balanceData['total_verified_balance'] ?? 0),
                    'timestamp' => now(),
                    'source' => 'balance_verification'
                ]);

                return response()->json([
                    'success' => true,
                    'data' => $balanceData
                ]);
            }

            // Fallback if Flask API doesn't have the endpoint
            return response()->json([
                'success' => true,
                'data' => [
                    'total_verified_balance' => 1000.00,
                    'available_verified_amount' => 10.00,
                    'deposit_only_mode' => true,
                    'double_check_enabled' => true,
                    'maximum_profit_mode' => true,
                    'message' => 'Using Laravel fallback balance data'
                ]
            ]);

        } catch (\Exception $e) {
            Log::error('Verified balance fetch failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Failed to fetch verified balance',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Handle bank transfers with deposit-only restrictions
     */
    public function bankTransfer(Request $request)
    {
        try {
            $request->validate([
                'exchange' => 'required|string',
                'amount' => 'required|numeric|min:0.01',
                'direction' => 'required|in:deposit,withdraw'
            ]);

            $exchange = $request->input('exchange');
            $amount = $request->input('amount');
            $direction = $request->input('direction');

            // Strict deposit-only policy
            if ($direction !== 'deposit') {
                TradeLog::create([
                    'level' => 'ERROR',
                    'message' => "BLOCKED WITHDRAWAL: Attempted to withdraw $$amount from $exchange",
                    'timestamp' => now(),
                    'source' => 'bank_transfer_security'
                ]);

                return response()->json([
                    'success' => false,
                    'error' => 'Withdrawals not permitted',
                    'message' => 'Deposit-only policy enforced. No withdrawals allowed.'
                ], 403);
            }

            // Log approved deposit
            TradeLog::create([
                'level' => 'INFO',
                'message' => "APPROVED DEPOSIT: $$amount to $exchange (deposit-only policy maintained)",
                'timestamp' => now(),
                'source' => 'bank_transfer'
            ]);

            // In a real implementation, this would interface with exchange APIs
            // For now, we approve deposits and log them

            return response()->json([
                'success' => true,
                'message' => 'Deposit approved and logged',
                'data' => [
                    'exchange' => $exchange,
                    'amount' => $amount,
                    'direction' => $direction,
                    'status' => 'approved',
                    'policy' => 'deposit-only'
                ]
            ]);

        } catch (\Illuminate\Validation\ValidationException $e) {
            return response()->json([
                'success' => false,
                'error' => 'Validation failed',
                'message' => $e->errors()
            ], 422);

        } catch (\Exception $e) {
            Log::error('Bank transfer failed: ' . $e->getMessage());

            TradeLog::create([
                'level' => 'ERROR',
                'message' => 'Bank transfer error: ' . $e->getMessage(),
                'timestamp' => now(),
                'source' => 'bank_transfer_error'
            ]);

            return response()->json([
                'success' => false,
                'error' => 'Bank transfer failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get conservative trading settings
     */
    public function tradingSettings()
    {
        try {
            $settings = [
                'verified_trade_amount' => env('VERIFIED_TRADE_AMOUNT', 10.00),
                'allow_extra_exchanges' => env('ALLOW_EXTRA_EXCHANGES', 'false') === 'true',
                'double_check_trades' => env('DOUBLE_CHECK_TRADES', 'true') === 'true',
                'deposit_only_mode' => env('DEPOSIT_ONLY_MODE', 'true') === 'true',
                'continuous_trading' => env('CONTINUOUS_TRADING', 'true') === 'true',
                'maximum_profit_mode' => env('MAXIMUM_PROFIT_MODE', 'true') === 'true',
                'take_profit_percent' => env('TAKE_PROFIT_PERCENT', 2.0),
                'stop_loss_percent' => env('STOP_LOSS_PERCENT', 0.5),
                'max_daily_loss_percent' => env('MAX_DAILY_LOSS_PERCENT', 2.0),
                'max_consecutive_losses' => env('MAX_CONSECUTIVE_LOSSES', 3),
                'min_trade_interval' => env('MIN_TRADE_INTERVAL', 60)
            ];

            return response()->json([
                'success' => true,
                'data' => $settings,
                'message' => 'Conservative trading settings retrieved'
            ]);

        } catch (\Exception $e) {
            Log::error('Trading settings fetch failed: ' . $e->getMessage());

            return response()->json([
                'success' => false,
                'error' => 'Failed to fetch trading settings',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get trading statistics with conservative metrics
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
            $totalFees = 0;
            foreach ($recentTrades as $trade) {
                if (preg_match('/[\+\-]\$([\d\.]+)/', $trade->message, $matches)) {
                    $amount = floatval($matches[1]);
                    if (strpos($trade->message, 'PROFITABLE') !== false) {
                        $totalProfit += $amount;
                    } elseif (strpos($trade->message, 'LOSS') !== false) {
                        $totalProfit -= $amount;
                    }
                }
                // Extract fee information if available
                if (preg_match('/Fee: \$([\d\.]+)/', $trade->message, $matches)) {
                    $totalFees += floatval($matches[1]);
                }
            }

            // Get conservative trading metrics
            $verifiedBalanceResponse = Http::timeout(5)->get("{$this->flaskUrl}/verified-balance");
            $verifiedBalance = $verifiedBalanceResponse->successful() ?
                $verifiedBalanceResponse->json() : ['total_verified_balance' => 0];

            return response()->json([
                'success' => true,
                'data' => [
                    'total_trades' => $totalTrades,
                    'profitable_trades' => $profitableTrades,
                    'win_rate' => round($winRate, 2),
                    'total_profit' => round($totalProfit, 2),
                    'total_fees' => round($totalFees, 2),
                    'net_profit' => round($totalProfit - $totalFees, 2),
                    'verified_balance' => $verifiedBalance['total_verified_balance'] ?? 0,
                    'conservative_mode' => true,
                    'deposit_only_policy' => true,
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