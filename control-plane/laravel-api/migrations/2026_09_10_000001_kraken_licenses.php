<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('kraken_licenses', function (Blueprint $table) {
            $table->id();
            $table->string('tentacle');
            $table->string('license_key')->unique();
            $table->unsignedBigInteger('user_id')->nullable();
            $table->timestamp('expires_at')->nullable();
            $table->boolean('revoked')->default(false);
            $table->timestamps();
            $table->index(['tentacle', 'license_key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kraken_licenses');
    }
};
