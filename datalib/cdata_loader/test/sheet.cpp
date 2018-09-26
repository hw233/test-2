#include "../src/sheet.h"
#include <iostream>
#include <assert.h>

using namespace std;

static int _test_sig_read_and_get_succeed()
{
    SignalSheet sheet("skill", {"id"});
    sheet.load("skill.csv");
    sheet.load("skill.csv");

    vector<string> data = sheet.get("10209013");
    int i = 0;
    cout << "get id=10209013:" << endl;
    for (auto d : data) {
        cout << "\t";
        cout << "type=" << sheet.attr_type(i) << ", ";
        cout << "name=" << sheet.attr_name(i) << ", ";
        cout << "value=" << d << endl;

        ++i;
    }
    
    assert(data.size() == 19);
    return 0;
}

static int _test_sig_get_failed_no_such_key()
{
    SignalSheet sheet("skill", {"id"});
    sheet.load("skill.csv");

    vector<string> data = sheet.get("9999");

    assert(data.size() == 0);
    return 0;
}

static int _test_sig_read_failed_cannt_open_file()
{
    SignalSheet sheet("skill", {"id"});
    assert(sheet.load("skilll.csv") == ECSV_CANNT_OPEN_FILE);
    return 0;
}

static int _test_sig_read_failed_key_not_in_name()
{
    SignalSheet sheet("skill", {"jjj"});

    assert(sheet.load("skill.csv") == ECSV_KEY_NOT_IN_ATTR);
    return 0;
}

static int _test_sig_read_failed_name_repeat()
{
    SignalSheet sheet("skill", {"id"});

    assert(sheet.load("skill.nr.csv") == ECSV_ATTR_REPEAT);
    return 0;
}

static int _test_sig_read_failed_attr_num_error()
{
    SignalSheet sheet("skill", {"id"});

    assert(sheet.load("skill.ne.csv") == ECSV_ATTR_NUM);
    return 0;
}

static int _test_com_read_and_get_succeed()
{
    ComplexSheet sheet("skill", "./", {"skill", "skill1"}, {"id"});

    assert(sheet.load() == SUCCEED);
    assert(sheet.load() == SUCCEED);

    vector<string> data = sheet.get("10209013");
    int i = 0;
    cout << "get id=10209013:" << endl;
    for (auto d : data) {
        cout << "\t";
        cout << "type=" << sheet.attr_type("10209013", i) << ", ";
        cout << "name=" << sheet.attr_name("10209013", i) << ", ";
        cout << "value=" << d << endl;

        ++i;
    }
    
    assert(data.size() == 19);
    return 0;
}

static int _test_com_get_failed_no_such_key()
{
    ComplexSheet sheet("skill", "./", {"skill", "skill1"}, {"id"});

    vector<string> data = sheet.get("10209013");
    assert(data.size() == 0);
    return 0;
}

static int _test_com_load_failed_cannt_open_file()
{
    ComplexSheet sheet("skill", "./", {"skill", "skill2"}, {"id"});
    assert(sheet.load() == ECSV_CANNT_OPEN_FILE);
    return 0;
}

static int _test_com_load_failed_attr_num_error()
{
    ComplexSheet sheet("skill", "./", {"skill.ne", "skill2"}, {"id"});
    assert(sheet.load() == ECSV_ATTR_NUM);
    return 0;
}


int main()
{
    _test_sig_read_and_get_succeed();
    cout << "signal sheet read and get succeed: OK" << endl;
    _test_sig_get_failed_no_such_key();
    cout << "signal sheet get failed of no such key: OK" << endl;
    _test_sig_read_failed_cannt_open_file();
    cout << "signal sheet get failed of cannt open file: OK" << endl;
    _test_sig_read_failed_key_not_in_name();
    cout << "signal sheet read failed key not in name: OK" << endl;
    _test_sig_read_failed_name_repeat();
    cout << "signal sheet read failed name repeat: OK" << endl;
    _test_sig_read_failed_attr_num_error();
    cout << "signal sheet read failed attr num error: OK" << endl;
    _test_com_read_and_get_succeed();
    cout << "complex sheet read and get succeed: OK" << endl;
    _test_com_get_failed_no_such_key();
    cout << "complex sheet get failed of no such key: OK" << endl;
    _test_com_load_failed_cannt_open_file();
    cout << "complex sheet get failed of cannt open file: OK" << endl;
    _test_com_load_failed_attr_num_error();
    cout << "complex sheet read failed attr num error: OK" << endl;

    return 0;
}
