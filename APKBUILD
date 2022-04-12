# Contributor: Johannes Krattenmacher <maloja@dev.krateng.ch>
# Maintainer: Johannes Krattenmacher <maloja@dev.krateng.ch>
pkgname=maloja
pkgver=3.0.0-dev
pkgrel=0
pkgdesc="Self-hosted music scrobble database"
url="https://github.com/krateng/maloja"
arch="noarch"
license="GPL-3.0"
depends="python3 tzdata"
pkgusers=$pkgname
pkggroups=$pkgname
depends_dev="gcc g++ python3-dev libxml2-dev libxslt-dev libffi-dev libc-dev py3-pip linux-headers"
makedepends="$depends_dev"
source="
	$pkgname-$pkgver.tar.gz::https://github.com/krateng/maloja/archive/refs/tags/v$pkgver.tar.gz
"
builddir="$srcdir"/$pkgname-$pkgver



build() {
	cd $builddir
	python3 -m build .
	pip3 install dist/*.tar.gz
}

package() {
	mkdir -p /etc/$pkgname || return 1
	mkdir -p /var/lib/$pkgname || return 1
	mkdir -p /var/cache/$pkgname || return 1
	mkdir -p /var/logs/$pkgname || return 1
}

# TODO
sha512sums="a674eaaaa248fc2b315514d79f9a7a0bac6aa1582fe29554d9176e8b551e8aa3aa75abeebdd7713e9e98cc987e7bd57dc7a5e9a2fb85af98b9c18cb54de47bf7  $pkgname-${pkgver}.tar.gz"
