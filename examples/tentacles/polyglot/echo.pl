use strict;
use JSON::PP;
my $raw = do { local $/; <STDIN> } // '{}';
$raw = '{}' unless length $raw;
my $req = decode_json($raw);
print encode_json({
  v => 1, id => $req->{id}, ok => JSON::PP::true,
  result => { arm => "echo-pl", lang => "perl", action => $req->{action}, echo => $req->{payload} // {} }
});
