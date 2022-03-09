# Contributor: Johannes Krattenmacher <maloja@dev.krateng.ch>
# Maintainer: Johannes Krattenmacher <maloja@dev.krateng.ch>
pkgname=maloja
pkgver=2.14.6
pkgrel=0
pkgdesc="Scrobble statistics server"
url="https://github.com/krateng/maloja"
arch="noarch"
license="GPL-3.0"
depends="python3 tzdata vips"
pkgusers=$pkgname
pkggroups=$pkgname
depends_dev="gcc python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers py3-build"
makedepends="$depends_dev"
source="
	maloja-$pkgver.tar.gz::https://github.com/krateng/maloja/archive/refs/tags/v$pkgver.tar.gz
"
builddir="$srcdir"/maloja-$pkgver



build() {
	cd $builddir
	python3 -m build .
	pip3 install dist/*.tar.gz
}

package() {
	mkdir -p /etc/maloja || return 1
	mkdir -p /var/lib/maloja || return 1
	mkdir -p /var/cache/maloja || return 1
	mkdir -p /var/logs/maloja || return 1
}

sha512sums="a674eaaaa248fc2b315514d79f9a7a0bac6aa1582fe29554d9176e8b551e8aa3aa75abeebdd7713e9e98cc987e7bd57dc7a5e9a2fb85af98b9c18cb54de47bf7  maloja-${pkgver}.tar.gz"
