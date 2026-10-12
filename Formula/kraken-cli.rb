class KrakenCli < Formula
  desc "Local-first CLI plugin runner. One binary. Many tentacles."
  homepage "https://kraken.topta.co"
  url "https://github.com/toptacos/kraken-builder/archive/refs/tags/v0.3.3.tar.gz"
  sha256 "0a2d9e1d7c46d65496994c3793bbcb674cf50ff5880e16eb9be6adbfa4f2e1b0"
  license "MIT"
  head "https://github.com/toptacos/kraken-builder.git", branch: "main"

  depends_on "python@3.12"

  def install
    # `examples` is 32 MB, and 16 MB of that is the hello-world demo's
    # vendored toolchains (rust, go) -- sources a user wanting the C demo
    # checks out from git, not something a package manager should ship.
    # `kraken vanilla` reads examples/tentacles, so that stays (including
    # the _template scaffold, which is two files and is how a user starts
    # a new tentacle).
    libexec.install Dir["kraken", "arms", "install.sh", "requirements.txt"]
    (libexec/"examples/tentacles").install Dir["examples/tentacles/*"].reject { |f|
      File.basename(f) == "hello-world"
    }
    (bin/"kraken").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="#{libexec}${PYTHONPATH:+:$PYTHONPATH}"
      exec "#{Formula["python@3.12"].opt_bin}/python3" -m kraken "$@"
    EOS
    chmod 0755, bin/"kraken"
    bin.install_symlink "kraken" => "k"
  end

  def post_install
    system bin/"kraken", "init"
    system bin/"kraken", "vanilla"
  end

  test do
    require "json"
    report = JSON.parse(shell_output("#{bin}/kraken doctor"))
    checks = report["checks"].to_h { |c| [c["name"], c] }

    # The install must resolve to this Cellar's libexec, not to a path frozen
    # when the formula was written. That regression shipped as
    # ModuleNotFoundError: No module named 'kraken'.
    source = checks.fetch("install.source")
    assert source["ok"], source["detail"]
    assert_match "libexec", source["detail"]

    # A pip kraken-cli anywhere on the Ruby-visible path can shadow this bin.
    assert checks["install.pip_kraken_cli"]["ok"],
           checks["install.pip_kraken_cli"]["detail"]
  end
end
