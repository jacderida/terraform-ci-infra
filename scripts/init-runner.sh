#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt update
retry_count=1
packages_installed="false"
while [[ $retry_count -le 20 ]]; do
  echo "Attempting to install packages..."
  # All these packages are necessary for a full build of all safe_network code,
  # including test binaries.
  sudo DEBIAN_FRONTEND=noninteractive apt install -y \
    build-essential docker.io git libssl-dev musl-tools pkg-config ripgrep unzip
  exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
      echo "packages installed successfully"
      packages_installed="true"
      break
  fi
  echo "Failed to install all packages."
  echo "Attempted $retry_count times. Will retry up to 20 times. Sleeping for 10 seconds."
  ((retry_count++))
  sleep 10
  # Without running this again there are times when it will just fail on every retry.
  sudo DEBIAN_FRONTEND=noninteractive apt update
done
if [[ "$packages_installed" == "false" ]]; then
  echo "Failed to install all packages"
  exit 1
fi

sudo systemctl enable docker
sudo usermod --groups docker ubuntu

curl -L -O https://static.rust-lang.org/rustup/dist/x86_64-unknown-linux-gnu/rustup-init
chmod +x rustup-init
./rustup-init --default-toolchain stable -y --no-modify-path
# Make Cargo related binaries available in a system-wide location.
# This prevents difficulties with having to source ~/.cargo/env in every shell
# step in an actions workflow.
sudo ln -s ~/.cargo/bin/* /usr/local/bin
rustup target add x86_64-unknown-linux-musl
