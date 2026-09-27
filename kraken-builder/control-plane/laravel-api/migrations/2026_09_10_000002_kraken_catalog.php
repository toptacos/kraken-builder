<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('kraken_catalog', function (Blueprint $table) {
            $table->id();
            $table->string('name')->unique();
            $table->string('version')->default('0.1.0');
            $table->string('source');
            $table->string('license')->default('free');
            $table->text('blurb')->nullable();
            $table->json('actions')->nullable();
            $table->string('author_email');
            $table->boolean('listed')->default(false);
            $table->timestamps();
        });

        Schema::create('kraken_beta', function (Blueprint $table) {
            $table->id();
            $table->string('email');
            $table->string('tentacle')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('kraken_beta');
        Schema::dropIfExists('kraken_catalog');
    }
};
