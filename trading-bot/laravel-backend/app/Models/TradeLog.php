<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class TradeLog extends Model
{
    use HasFactory;

    protected $fillable = [
        'level',
        'message',
        'timestamp',
        'source',
        'trade_data'
    ];

    protected $casts = [
        'timestamp' => 'datetime',
        'trade_data' => 'array'
    ];

    /**
     * Get logs by level
     */
    public function scopeByLevel($query, $level)
    {
        return $query->where('level', strtoupper($level));
    }

    /**
     * Get recent logs
     */
    public function scopeRecent($query, $hours = 24)
    {
        return $query->where('created_at', '>=', now()->subHours($hours));
    }

    /**
     * Get logs by source
     */
    public function scopeBySource($query, $source)
    {
        return $query->where('source', $source);
    }
}