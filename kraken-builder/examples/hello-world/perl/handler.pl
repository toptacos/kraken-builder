#!/usr/bin/env perl
use strict;
use warnings;
use JSON::PP;
my $raw = do { local $/; <STDIN> };
$raw = '{}' unless defined $raw && length $raw;
my $req = decode_json($raw);
my $name = ($req->{payload}{name} // 'world');
print encode_json({ v => 1, id => $req->{id}, ok => JSON::PP::true, result => { arm => 'hello-pl', lang => 'perl', hello => "hello, $name" } });
