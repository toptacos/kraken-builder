<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('kraken_contact', function (Blueprint $table) {
            $table->id();
            $table->string('email');
            $table->text('body');
            $table->string('scope')->default('global');
            $table->string('source')->default('panel');
            $table->timestamps();
        });

        Schema::table('kraken_users', function (Blueprint $table) {
            $table->string('org_key')->nullable()->unique();
        });
    }

    public function down(): void
    {
        Schema::table('kraken_users', function (Blueprint $table) {
            $table->dropColumn('org_key');
        });
        Schema::dropIfExists('kraken_contact');
    }
};
