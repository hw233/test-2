#build cdata_loader

CXX= g++ -std=c++11
CPPFLAGS= -O2 -Wall -fPIC -Ilibjsoncpp/ -I/usr/include/python2.7

LIB_JSONCPP_FLAG= -Llibjsoncpp -ljsoncpp

CDATA_LOADER_SO= ./cdata_loader.so
CDATA_LOADER_O= src/sheet.o src/loader.o
INIT_O= src/init.o

TEST_SHEET_BIN= test/sheet.out
TEST_SHEET_O= test/sheet.o
TEST_LOADER_O= test/loader.o
TEST_LOADER_BIN= test/loader.out

all: $(CDATA_LOADER_SO) make_test

$(CDATA_LOADER_SO): $(CDATA_LOADER_O) $(INIT_O)
	$(CXX) -shared -o $@ $(CDATA_LOADER_O) $(INIT_O) $(LIB_JSONCPP_FLAG)

make_test: $(TEST_SHEET_BIN) $(TEST_LOADER_BIN)

$(TEST_SHEET_BIN): $(CDATA_LOADER_O) $(TEST_SHEET_O)
	$(CXX) -o $@ $(CDATA_LOADER_O) $(TEST_SHEET_O) $(LIB_JSONCPP_FLAG)

$(TEST_LOADER_BIN): $(CDATA_LOADER_O) $(TEST_LOADER_O)
	$(CXX) -o $@ $(CDATA_LOADER_O) $(TEST_LOADER_O) $(LIB_JSONCPP_FLAG)

src/init.o: src/init.cpp src/loader.h
src/loader.o: src/loader.cpp src/loader.h src/sheet.h
src/sheet.o: src/sheet.cpp src/sheet.h

test/sheet.o: test/sheet.cpp src/sheet.h
test/loader.o: test/loader.cpp src/loader.h

test: all
	cd test && valgrind --tool=memcheck ./sheet.out
	cd test && valgrind --tool=memcheck ./loader.out
	cd test && python test.py

clean:
	rm -f $(CDATA_LOADER_O) $(INIT_O) \
		$(TEST_SHEET_BIN) $(TEST_SHEET_O) \
		$(TEST_LOADER_BIN) $(TEST_LOADER_O)

.PHONY: all clean test
