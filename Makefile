NAME=watchdog-fs
VERSION=0.5
FILES=$(wildcard *.py) etc/ actions.d/
rpm:
	find . | grep __pycache__ | xargs rm -rf
	rm -rf build
	mkdir -p build/${NAME}-${VERSION}
	cp -r $(FILES) build/${NAME}-${VERSION}
	tar czvf ~/rpmbuild/SOURCES/${NAME}-${VERSION}.tar.gz -C build ${NAME}-${VERSION} 
	rm -rf build
	rpmbuild -ba watchdog-fs.spec
	
