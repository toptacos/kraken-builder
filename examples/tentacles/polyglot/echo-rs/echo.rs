// Compile: rustc -o echo-rs echo.rs
// Then point tentacle.yaml binary at echo-rs.
use std::io::{self, Read};
fn main() {
    let mut s = String::new();
    io::stdin().read_to_string(&mut s).ok();
    if s.is_empty() { s = "{}".into(); }
    print!("{{\"v\":1,\"ok\":true,\"result\":{{\"arm\":\"echo-rs\",\"lang\":\"rust\"}}}}");
}
