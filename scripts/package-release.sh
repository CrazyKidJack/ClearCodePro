#!/usr/bin/env bash

set -euo pipefail

version="${1:-}"
semver_pattern='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?(\+([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?$'

if [[ ! "${version}" =~ ${semver_pattern} ]]; then
  echo "Invalid Semantic Version: ${version}" >&2
  echo "Use a version such as 1.0.0, 1.1.0-beta.1, or 2.0.0+build.1." >&2
  exit 1
fi

# Semantic Versioning forbids leading zeroes in numeric pre-release identifiers.
if [[ "${version}" == *-* ]]; then
  prerelease="${version#*-}"
  prerelease="${prerelease%%+*}"
  IFS='.' read -r -a identifiers <<< "${prerelease}"
  for identifier in "${identifiers[@]}"; do
    if [[ "${identifier}" =~ ^[0-9]+$ && "${#identifier}" -gt 1 && "${identifier}" == 0* ]]; then
      echo "Invalid Semantic Version: numeric pre-release identifier '${identifier}' has a leading zero." >&2
      exit 1
    fi
  done
fi

package_name="ClearCodePro-v${version}"
dist_dir="${DIST_DIR:-dist}"
archive="${dist_dir}/${package_name}.zip"

rm -f -- "${archive}"
mkdir -p "${dist_dir}"

font_count="$(git ls-files 'fonts/*.ttf' | wc -l | tr -d ' ')"
if [[ "${font_count}" != "42" ]]; then
  echo "Expected 42 TTF files, found ${font_count}." >&2
  exit 1
fi

for required_file in README.md LICENSE.txt FONTLOG.txt; do
  if ! git ls-files --error-unmatch "${required_file}" >/dev/null 2>&1; then
    echo "Missing required release file: ${required_file}" >&2
    exit 1
  fi
done

git archive \
  --format=zip \
  --prefix="${package_name}/" \
  --output="${archive}" \
  HEAD \
  -- fonts README.md LICENSE.txt FONTLOG.txt

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "archive=${archive}" >> "${GITHUB_OUTPUT}"
fi

echo "Created ${archive} with ${font_count} font files."
