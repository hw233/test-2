#include "../src/loader.h"
#include <iostream>
#include <assert.h>
#include <vector>
#include <time.h>
#include <math.h>

using namespace std;

int _test_efficiency()
{
    Loader loader("test_conf.json", "test");
    loader.load();

    vector<const char*> keys = loader.get_keys("skill");
    int k = 0;

    for (int i = 2; i <= 6; ++i) {
        int count = pow(10, i);
        clock_t t1 = clock();
        for (int j = 0; j < count; ++j) {
            loader.get("skill" ,keys[k % keys.size()]);
            ++k;
        }
        clock_t t2 = clock();
        cout << "get " << count << " consume " 
            << (t2 - t1) / static_cast<double>(CLOCKS_PER_SEC) << "(s)" << endl;
    }
    return 0;
}

int main()
{
    _test_efficiency();
}