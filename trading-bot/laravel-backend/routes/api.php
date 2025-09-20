<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\TradingController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "api" middleware group. Make something great!
|
*/

Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

// Trading Bot API Routes
Route::prefix('trading')->group(function () {
    Route::get('/dashboard', [TradingController::class, 'dashboard']);
    Route::get('/logs', [TradingController::class, 'logs']);
    Route::get('/statistics', [TradingController::class, 'statistics']);
    Route::post('/test-trade', [TradingController::class, 'testTrade']);
    Route::post('/run-cycle', [TradingController::class, 'runCycle']);
});

// Health check
Route::get('/health', function () {
    return response()->json([
        'status' => 'healthy',
        'service' => 'laravel-backend',
        'timestamp' => now()->toISOString()
    ]);
});