<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('kraken_users', function (Blueprint $table) {
            $table->id();
            $table->string('email')->unique();
            $table->string('plan')->default('free');
            $table->timestamps();
        });

        Schema::create('kraken_devices', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id');
            $table->string('device_id')->unique();
            $table->string('kind')->default('cli');
            $table->string('name')->nullable();
            $table->string('push_token')->nullable();
            $table->boolean('push_opt_in')->default(false);
            $table->timestamps();
        });

        Schema::create('kraken_sessions', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id');
            $table->json('pinboard')->nullable();
            $table->timestamps();
        });

        Schema::create('kraken_run_queue', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id');
            $table->string('target_device');
            $table->string('tentacle');
            $table->string('action');
            $table->json('payload')->nullable();
            $table->string('status')->default('queued');
            $table->json('result')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kraken_run_queue');
        Schema::dropIfExists('kraken_sessions');
        Schema::dropIfExists('kraken_devices');
        Schema::dropIfExists('kraken_users');
    }
};
