build: important_separators.cpp
	g++-14 -std=gnu++23 important_separators.cpp
	mv a.out enclose

o3: important_separators.cpp
	g++-14 -std=gnu++23 important_separators.cpp -O3
	mv a.out enclose

clean:
	rm -f a.out enclose
