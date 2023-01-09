#!/bin/sh

set -eux

# Build the requested version of libyaml locally
echo "::group::fetch libyaml ${LIBYAML_REF}"
git config --global advice.detachedHead false
git clone --branch "$LIBYAML_REF" "$LIBYAML_REPO" libyaml

# Use a subshell to avoid polluting the current directory
(
    set -eux
    cd libyaml || true
    git reset --hard "$LIBYAML_REF"
    echo "::endgroup::"

    # Build only a static library - this reduces our reliance on auditwheel/delocate magic
    echo "::group::autoconf libyaml w/ static only"
    ./bootstrap
    ./configure --disable-dependency-tracking --with-pic --enable-shared=no
    echo "::endgroup::"

    echo "::group::build libyaml"
    make
    echo "::endgroup::"

    echo "::group::test built libyaml"
    make test-all
    echo "::endgroup::"
)
