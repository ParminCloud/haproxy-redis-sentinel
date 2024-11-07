{ pkgs, lib, config, inputs, ... }:

{
  packages = with pkgs; [ git helm-docs ];

  # languages.rust.enable = true;
  languages = {
    python = {
      version = "3.12";
      enable = true;
      poetry = {
          enable = true;
          activate = {
            enable = true;
          };
          install = {
            enable = true;
          };
        };
    };
  };
  # https://devenv.sh/scripts/
  scripts = {};

  enterShell = ''
    git status
    poetry install
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
  '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
