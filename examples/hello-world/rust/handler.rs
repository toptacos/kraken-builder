use std::io::{self, Read};
fn main() {
    let mut s = String::new();
    let _ = io::stdin().read_to_string(&mut s);
    let name = extract(&s).unwrap_or("world");
    print!("{{\"v\":1,\"ok\":true,\"result\":{{\"arm\":\"hello-rs\",\"lang\":\"rust\",\"hello\":\"hello, {}\"}}}}", name);
}
fn extract(s: &str) -> Option<&str> {
    let key = "\"name\"";
    let i = s.find(key)?;
    let rest = &s[i + key.len()..];
    let q = rest.find('"')?;
    let rest = &rest[q + 1..];
    let q2 = rest.find('"')?;
    Some(&rest[..q2])
}
