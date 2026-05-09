#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-local-skill.sh --target DIR [--mode copy|symlink] [--real] [--no-backup]

Installs skills/dao-governance into an agents-style skill directory.

Examples:
  scripts/install-local-skill.sh --target /tmp/degov-agent-skills-home --mode copy
  scripts/install-local-skill.sh --target /tmp/degov-agent-skills-home --mode symlink
  scripts/install-local-skill.sh --real --mode copy

By default --target DIR means DIR is an isolated agents home and the skill is
installed to DIR/skills/dao-governance. With --real, the target defaults to
~/.agents and an existing ~/.agents/skills/dao-governance is backed up first.
EOF
}

mode="copy"
target=""
real_install=false
backup=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --mode)
      mode="${2:-}"
      shift 2
      ;;
    --real)
      real_install=true
      shift
      ;;
    --no-backup)
      backup=false
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$mode" != "copy" && "$mode" != "symlink" ]]; then
  echo "--mode must be copy or symlink" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${repo_root}/skills/dao-governance"

if [[ "$real_install" == true ]]; then
  target="${target:-${HOME}/.agents}"
elif [[ -z "$target" ]]; then
  echo "--target is required unless --real is used" >&2
  usage >&2
  exit 2
fi

install_root="${target}/skills"
destination="${install_root}/dao-governance"

echo "source: ${source_dir}"
echo "target: ${destination}"
echo "mode: ${mode}"

mkdir -p "$install_root"

if [[ -e "$destination" || -L "$destination" ]]; then
  if [[ "$real_install" == true && "$backup" == true ]]; then
    backup_path="${destination}.backup-$(date +%Y%m%d-%H%M%S)"
    cp -a "$destination" "$backup_path"
    echo "backup: ${backup_path}"
  fi
  rm -rf "$destination"
fi

if [[ "$mode" == "symlink" ]]; then
  ln -s "$source_dir" "$destination"
else
  mkdir -p "$destination"
  tar --exclude='node_modules' --exclude='.pnpm-store' -C "$source_dir" -cf - . | tar -C "$destination" -xf -
fi

if [[ "$mode" == "copy" && -d "${destination}/scripts/node_modules" ]]; then
  echo "ERROR: node_modules should not be installed into the skill copy" >&2
  exit 1
fi

printf 'installed_path=%s\n' "$destination"
