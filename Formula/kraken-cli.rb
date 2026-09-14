class KrakenCli < Formula
  desc "Local-first CLI plugin runner. One binary. Many tentacles."
  homepage "https://kraken.topta.co"
  url "https://github.com/toptacos/kraken-builder/archive/refs/tags/v0.1.1.tar.gz"
  sha256 "8a9d4a9cecb783439974d5cbb9fb807be94d12177013d5d60cbedb96906e06e5"
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
    output = shell_output("#{bin}/kraken self plan")
    assert_match "ok", output
  end
end
