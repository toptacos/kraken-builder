<?php
/**
 * Drop into the existing api.topta.co Laravel app.
 *
 * RouteServiceProvider or bootstrap/app.php:
 *   require base_path('routes/kraken.php');
 *
 * Expected table (Postgres):
 *   kraken_licenses (id, tentacle, license_key, user_id, expires_at, revoked)
 */

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::prefix('api/kraken')->group(function () {
    Route::post('/contact', function (Request $request) {
        $email = (string) $request->input('email');
        $body = (string) $request->input('body');
        $scope = (string) $request->input('scope', 'global');
        $source = (string) $request->input('source', 'panel');
        if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || $body === '') {
            return response()->json(['ok' => false, 'error' => ['message' => 'email and body required']], 422);
        }
        DB::table('kraken_contact')->insert([
            'email' => $email,
            'body' => substr($body, 0, 4000),
            'scope' => $scope,
            'source' => $source,
            'created_at' => now(),
            'updated_at' => now(),
        ]);
        return response()->json(['ok' => true, 'sent' => true, 'source' => $source]);
    });

    Route::get('/devices', function (Request $request) {
        $key = (string) ($request->header('X-Kraken-Org-Key') ?: $request->bearerToken() ?: $request->query('org_key', ''));
        if ($key === '') {
            return response()->json(['ok' => false, 'error' => ['message' => 'org key required']], 401);
        }
        $userId = DB::table('kraken_users')->where('org_key', $key)->value('id');
        if (!$userId) {
            return response()->json(['ok' => false, 'error' => ['message' => 'invalid org key']], 403);
        }
        $rows = DB::table('kraken_devices')->where('user_id', $userId)->orderBy('updated_at', 'desc')->get();
        return response()->json(['ok' => true, 'devices' => $rows]);
    });

    Route::post('/licenses/verify', function (Request $request) {
        $tentacle = (string) $request->input('tentacle');
        $key = (string) $request->input('key');
        if ($tentacle === '' || $key === '') {
            return response()->json(['ok' => false, 'error' => ['message' => 'missing tentacle or key']], 422);
        }

        $row = DB::table('kraken_licenses')
            ->where('tentacle', $tentacle)
            ->where('license_key', $key)
            ->where(function ($q) {
                $q->whereNull('revoked')->orWhere('revoked', false);
            })
            ->first();

        if (!$row) {
            return response()->json(['ok' => false, 'error' => ['message' => 'invalid license']], 403);
        }

        return response()->json([
            'ok' => true,
            'tentacle' => $tentacle,
            'expires_at' => $row->expires_at ?? null,
        ]);
    });

    Route::get('/catalog', function () {
        $rows = DB::table('kraken_catalog')->orderBy('name')->get();
        return response()->json(['ok' => true, 'tentacles' => $rows]);
    });

    Route::post('/catalog/register', function (Request $request) {
        $name = strtolower((string) $request->input('name'));
        $source = (string) $request->input('source');
        $email = (string) $request->input('author_email');
        if ($name === '' || $source === '' || $email === '') {
            return response()->json(['ok' => false, 'error' => ['message' => 'name, source, author_email required']], 422);
        }
        if (!preg_match('/^[a-z0-9-]+$/', $name)) {
            return response()->json(['ok' => false, 'error' => ['message' => 'name must be lowercase hyphenated']], 422);
        }
        DB::table('kraken_catalog')->updateOrInsert(
            ['name' => $name],
            [
                'version' => (string) $request->input('version', '0.1.0'),
                'source' => $source,
                'license' => (string) $request->input('license', 'free'),
                'blurb' => (string) $request->input('blurb', ''),
                'actions' => json_encode($request->input('actions', [])),
                'author_email' => $email,
                'listed' => false,
            ]
        );
        return response()->json(['ok' => true, 'name' => $name, 'listed' => false, 'note' => 'held for review']);
    });

    Route::post('/licenses/issue', function (Request $request) {
        $tentacle = (string) $request->input('tentacle');
        $plan = (string) $request->input('plan', 'beta');
        $email = (string) $request->input('email');
        if ($tentacle === '') {
            return response()->json(['ok' => false, 'error' => ['message' => 'missing tentacle']], 422);
        }
        $paid = $plan !== 'beta' && env('STRIPE_SECRET') && env('KRAKEN_BILLING') === '1';
        if ($paid) {
            return response()->json([
                'ok' => false,
                'error' => ['message' => 'complete checkout', 'checkout' => url('/api/kraken/billing/checkout')],
            ], 402);
        }
        $key = 'k_' . bin2hex(random_bytes(16));
        DB::table('kraken_licenses')->insert([
            'tentacle' => $tentacle,
            'license_key' => $key,
            'expires_at' => now()->addYear(),
            'revoked' => false,
            'created_at' => now(),
            'updated_at' => now(),
        ]);
        return response()->json(['ok' => true, 'key' => $key, 'tentacle' => $tentacle, 'plan' => $plan]);
    });

    Route::post('/beta', function (Request $request) {
        $email = (string) $request->input('email');
        if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return response()->json(['ok' => false, 'error' => 'valid email required'], 422);
        }
        DB::table('kraken_beta')->insert([
            'email' => $email,
            'tentacle' => (string) $request->input('tentacle', ''),
            'created_at' => now(),
            'updated_at' => now(),
        ]);
        return response()->json(['ok' => true]);
    });

    Route::post('/billing/checkout', function (Request $request) {
        if (!env('STRIPE_SECRET') || env('KRAKEN_BILLING') !== '1') {
            return response()->json([
                'ok' => false,
                'error' => ['message' => 'billing off — set STRIPE_SECRET and KRAKEN_BILLING=1 after a test-mode key'],
            ], 503);
        }
        return response()->json([
            'ok' => false,
            'error' => ['message' => 'wire Checkout Session here; do not enable live charges from CI'],
        ], 501);
    });

    Route::post('/session/login', function (Request $request) {
        $email = strtolower((string) $request->input('email'));
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return response()->json(['ok' => false, 'error' => 'email'], 422);
        }
        $id = DB::table('kraken_users')->where('email', $email)->value('id');
        if (!$id) {
            $id = DB::table('kraken_users')->insertGetId([
                'email' => $email,
                'plan' => 'free',
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
        $device = (string) $request->input('device_id', '');
        if ($device !== '') {
            DB::table('kraken_devices')->updateOrInsert(
                ['device_id' => $device],
                [
                    'user_id' => $id,
                    'kind' => (string) $request->input('kind', 'cli'),
                    'name' => (string) $request->input('device_name', 'cli'),
                    'updated_at' => now(),
                ]
            );
        }
        return response()->json(['ok' => true, 'user_id' => $id, 'plan' => 'free']);
    });

    Route::post('/session/sync', function (Request $request) {
        $email = strtolower((string) $request->input('email'));
        $user = DB::table('kraken_users')->where('email', $email)->first();
        if (!$user) {
            return response()->json(['ok' => false, 'error' => 'login first'], 401);
        }
        DB::table('kraken_sessions')->updateOrInsert(
            ['user_id' => $user->id],
            ['pinboard' => json_encode($request->input('pinboard', [])), 'updated_at' => now()]
        );
        return response()->json(['ok' => true, 'user_id' => $user->id]);
    });

    Route::post('/devices/push', function (Request $request) {
        $device = (string) $request->input('device_id');
        if ($device === '') {
            return response()->json(['ok' => false], 422);
        }
        DB::table('kraken_devices')->where('device_id', $device)->update([
            'push_token' => (string) $request->input('token', ''),
            'push_opt_in' => (bool) $request->input('opt_in', false),
            'updated_at' => now(),
        ]);
        return response()->json(['ok' => true, 'vendor' => 'stub']);
    });

    Route::post('/queue', function (Request $request) {
        $email = strtolower((string) $request->input('email'));
        $user = DB::table('kraken_users')->where('email', $email)->first();
        if (!$user) {
            return response()->json(['ok' => false, 'error' => 'login first'], 401);
        }
        $id = DB::table('kraken_run_queue')->insertGetId([
            'user_id' => $user->id,
            'target_device' => (string) $request->input('target_device'),
            'tentacle' => (string) $request->input('tentacle'),
            'action' => (string) $request->input('action'),
            'payload' => json_encode($request->input('payload', [])),
            'status' => 'queued',
            'created_at' => now(),
            'updated_at' => now(),
        ]);
        return response()->json(['ok' => true, 'id' => $id, 'status' => 'queued']);
    });
});

