import sys
sys.path.append("..")
import cdata_loader
import time

def _test_load_and_get_succeed():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()
    cdata_loader.load()

    data = cdata_loader.get('skill', '10209013')
    assert len(data) == 17
    assert data['id'] == 10209013

    cdata_loader.destroy()
    cdata_loader.destroy()

def _test_load_and_get_keys_succeed():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()

    keys = cdata_loader.get_keys('skill')
    assert len(keys) == 200
    assert 10209013 in keys

    cdata_loader.destroy()

def _test_load_failed_bad_json():
    cdata_loader.init('test_conf.bad.json', 'test')
    try:
        cdata_loader.load()
    except Exception as e:
        assert e.message == 'Bad json file'

    cdata_loader.destroy()

def _test_load_failed_bad_conf():
    cdata_loader.init('test_conf.econf.json', 'test')
    try:
        cdata_loader.load()
    except Exception as e:
        assert e.message == 'Keys len < 1'

    cdata_loader.destroy()

def _test_load_failed_bad_csv():
    cdata_loader.init('test_conf.ecsv.json', 'test')
    try:
        cdata_loader.load()
    except Exception as e:
        assert e.message == 'Csv file isn\'t a matrix'

    cdata_loader.destroy()

def _test_load_failed_cannt_open_file():
    cdata_loader.init('test_conf.json', 'teast')
    try:
        cdata_loader.load()
    except Exception as e:
        assert e.message == 'Can\'t open data file'

    cdata_loader.destroy()

def _test_get_failed_no_such_key():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()

    data = cdata_loader.get('skill', 'aaa')
    assert data == {}

    cdata_loader.destroy()

def _test_get_failed_no_such_sheet():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()

    data = cdata_loader.get('skilll', '10209013')
    assert data == {}

    cdata_loader.destroy()

def _test_get_keys_failed_no_such_sheet():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()

    keys = cdata_loader.get_keys('skilll')
    assert keys == []

    cdata_loader.destroy()

def _test_efficiency():
    cdata_loader.init('test_conf.json', 'test')
    cdata_loader.load()

    keys = cdata_loader.get_keys('skill')
    keys = [str(k) for k in keys]
    k = 0

    for i in xrange(2, 6):
        count = 10 ** i
        t1 = time.time()
        for j in xrange(count):
            cdata_loader.get('skill', keys[k % len(keys)])
            #cdata_loader.get('skill', '10209013')
            k += 1

        t2 = time.time()
        print 'get %d consume %s' % (count, t2 - t1)

    cdata_loader.destroy()

if __name__ == '__main__':
    _test_load_and_get_succeed()
    print 'load and get succeed: OK'
    _test_load_and_get_keys_succeed()
    print 'load and get keys succeed: OK'
    _test_load_failed_bad_json()
    print 'load failed of bad json: OK'
    _test_load_failed_bad_conf()
    print 'load failed of bad conf: OK'
    _test_load_failed_bad_csv()
    print 'load failed of bad csv: OK'
    _test_load_failed_cannt_open_file()
    print 'load failed of cannt open file: OK'
    _test_get_failed_no_such_key()
    print 'get failed of no such key: OK'
    _test_get_failed_no_such_sheet()
    print 'get failed of no such sheet: OK'
    _test_get_keys_failed_no_such_sheet()
    print 'get keys failed of no shuc sheet: OK'
    _test_efficiency()
