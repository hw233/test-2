/**
 * Created on 2017-03-30
 * @Author: huangluyu(huangluyu@ice-time.cn)
 * @Brief : loader 类
 */

#include "loader.h"
#include <fstream>

using namespace std;
using namespace Json;

const vector<string> Loader::empty_vector;
const char *Loader::empty_str = "";

vector<string> Loader::jsonvalue2vector(const Value &value)
{
    vector<string> ret;
    for (const auto &v : value)
        ret.push_back(v.asString().c_str());

    return ret;
}

Loader::~Loader()
{
    for (const auto &s : sheets)
        delete s.second;
}

int Loader::load()
{
    if (is_loaded)
        return SUCCEED;

    Reader reader;
    Value root;
    ifstream iconf;

    iconf.open(conf);
    if (!iconf.is_open())
        return ECONF_CANNT_OPEN_FILE;

    if (!reader.parse(iconf, root, false)) {
        iconf.close();
        return ECONF_BAD_JSON;
    }

    string path = root["path"][version.c_str()].asString().c_str();

    Value files = root["files"];
    for (const auto &file : files) {
        Value dicts = file["dicts"];
        for (const auto &dict : dicts) {
            vector<string> sheets = jsonvalue2vector(dict["sheets"]);
            vector<string> key = jsonvalue2vector(dict["key"]);
            
            if (sheets.size() < 1) {
                iconf.close();
                return ECONF_SHEETS_LEN;
            }
            if (key.size() < 1) {
                iconf.close();
                return ECONF_KEY_LEN;
            }

            string name = dict["name"].asString() == "" ?
                sheets[0] : dict["name"].asString().c_str();
            
            //ComplexSheet sheet(name.c_str(), path.c_str(), sheets, key);
            ComplexSheet *sheet = new ComplexSheet(name.c_str(), path.c_str(), sheets, key);
            int ret = sheet->load();
            if (ret != SUCCEED) {
                iconf.close();
                delete sheet;
                return ret;
            }
            this->sheets[name] = sheet;
        }
    }
    iconf.close();
    is_loaded = true;
    return SUCCEED;
}


const vector<string> &Loader::get(const char *sheet, const char *key)
{
    map<string, ComplexSheet*>::iterator it;
    return (it = sheets.find(sheet)) == sheets.end() ? empty_vector : it->second->get(key);
}

vector<const char*> Loader::get_keys(const char *sheet)
{
    map<string, ComplexSheet*>::iterator it;
    return (it = sheets.find(sheet)) == sheets.end() ? vector<const char*>() : it->second->get_keys();
}

int Loader::attr_type(const char *sheet, const char *key, size_t index)
{
    map<string, ComplexSheet*>::iterator it;
    return (it = sheets.find(sheet)) == sheets.end() ? 0 : it->second->attr_type(key, index);
}

int Loader::key_type(const char *sheet)
{
    map<string, ComplexSheet*>::iterator it;
    return (it = sheets.find(sheet)) == sheets.end() ? 0 : it->second->key_type();
}

string Loader::attr_name(const char *sheet, const char *key, size_t index)
{
    map<string, ComplexSheet*>::iterator it;
    return (it = sheets.find(sheet)) == sheets.end() ? empty_str : it->second->attr_name(key, index);
}
