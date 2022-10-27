#!/bin/bash

sudo DEBIAN_FRONTEND=noninteractive apt update
retry_count=1
packages_installed="false"
while [[ $retry_count -le 20 ]]; do
  echo "Attempting to install packages..."
  sudo DEBIAN_FRONTEND=noninteractive apt install docker.io git -y
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
