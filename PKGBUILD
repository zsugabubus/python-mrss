pkgname=python-mrss
pkgver=0
pkgrel=1
pkgdesc='RSS to email'
arch=(any)
license=(Unlicense)
depends=(python-feedparser)
makedepends=(python-build python-installer python-poetry-core)
source=("git+file://$HOME/src/$pkgname")
sha256sums=(SKIP)

prepare() {
	cd "$pkgname"
	poetry build
}

pkgver() {
	cd "$pkgname"
	poetry version -s
}

build() {
	cd "$pkgname"
	python -m build --wheel --skip-dependency-check --no-isolation
}

package() {
	cd "$pkgname"
	python -m installer --destdir="$pkgdir" dist/*.whl
}
