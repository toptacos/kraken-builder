class KrakenCli < Formula
  desc "Local-first CLI plugin runner. One binary. Many tentacles."
  homepage "https://kraken.topta.co"
  url "https://github.com/toptacos/kraken-builder/archive/refs/tags/v0.3.1.tar.gz"
  sha256 "e2a4bd5af1c6b2c8ce509a3d48eea5fdf830f7d75de315b99d628dc8243f5fee"
  license "MIT"
  head "https://github.com/toptacos/kraken-builder.git", branch: "main"

  depends_on "python@3.12"

  def install
    libexec.install Dir["kraken", "examples", "arms", "install.sh", "requirements.txt"]
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
