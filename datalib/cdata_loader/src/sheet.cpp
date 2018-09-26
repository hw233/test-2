/**
 * Created on 2017-03-30
 * @Author: huangluyu(huangluyu@ice-time.cn)
 * @Brief : sheet, 包括单个sheet和复合sheet
 */

#include "sheet.h"
#include <fstream>
#include <stdexcept>
#include <iostream>
#include <algorithm>
#include <set>

using namespace std;

#define SEP ","
#define SEP_C ','
#define CSV_FILE_NAME(sheet) (sheet + ".csv")

const vector<string> SignalSheet::empty_vector;
const char *SignalSheet::empty_str = "";

/*读csv文件*/
int SignalSheet::load(const char *file)
{
    ifstream ifile;
    ifile.open(file);

    if (key_names.size() <= 0) {
        cerr << "Error sheet:" << name << endl;
        return ECONF_KEY_LEN;
    }

    if (name == "") {
        cerr << "Error sheet:" << name << endl;
        return ECONF_NONE_NAME;
    }

    if (!ifile.is_open()) {
        cerr << "Error sheet:" << name << endl;
        return ECSV_CANNT_OPEN_FILE;
    }

    string line;
    int i = 0;
    _last_line_len = -1;

    try {
        while (getline(ifile, line)) {
            if (line.empty())
                continue;
            if (line[line.size() - 1] == '\n' || line[line.size() - 1] == '\r')
                line = line.substr(0, line.size() - 1);

            if (i == 0)
                parse_type(line);
            else if (i == 1)
                parse_name(line);
            else
                parse_data(line);

            ++i;
        }
    } catch (int e) {
        ifile.close();
        cerr << "Error sheet:" << name << endl;
        return e;
    }
    ifile.close();
    return SUCCEED;
}

/**
 * 解析csv的每一行
 * 仅简单分割,不支持引号转义
 */
vector<string> SignalSheet::parse_line(string line)
{
    int len = count(line.begin(), line.end(), SEP_C) + 1;
    int i = 0;

    vector<string> split_list(len);
    if (line != "") {
        line += SEP;
        int pos;
        for (int pre_pos = 0; (pos = line.find(SEP)) != -1;) {
            split_list[i] = line.substr(pre_pos, pos);
            line = line.substr(pos + 1);
            ++i;
        }
    }
    
    if (_last_line_len != -1 && _last_line_len != static_cast<int>(split_list.size()))
        throw ECSV_ATTR_NUM;
    
    _last_line_len = split_list.size();
    return split_list;
}

int SignalSheet::parse_name(const string &line)
{
    vector<string> name_row = parse_line(line);

    key_type = TYPE_STRING;

    //校验:
    //  1.是否key都在name中
    //  2.name是否有重复
    bool once = true;
    map<string, int> repeat;
    size_t key_in_name = 0;
    int i = 0;
    for (const auto &k : key_names) {
        for (const auto &name : name_row) {
            if (once) {
                if (key_names.size() == 1 && name == key_names[0])
                    key_type = types[i];

                names.push_back(name);
                repeat[name] += 1;
                ++i;
            }
            if (k == name)
                ++key_in_name;
        }
        once = false;
    }

    if (key_in_name < key_names.size())
        throw ECSV_KEY_NOT_IN_ATTR;
    for (const auto &r : repeat)
        if (r.second != 1)
            throw ECSV_ATTR_REPEAT;

    return 0;
}

int SignalSheet::parse_type(const string &line)
{
    vector<string> type_row = parse_line(line);
    int t;
    for (const auto &type : type_row) {
        if (type == "System.Int32") {
            t = TYPE_INT32;
        } else if (type == "System.Single") {
            t = TYPE_SINGLE;
        } else if (type == "System.String") {
            t = TYPE_STRING;
        } else if (type == "System.Int32[]") {
            t = TYPE_INT32_ARRAY;
        } else if (type == "System.Single[]") {
            t = TYPE_SINGLE_ARRAY;
        } else if (type == "System.String[]") {
            t = TYPE_STRING_ARRAY;
        } else if (type == "System.Boolean") {
            t = TYPE_BOOLEAN;
        } else
            throw ECSV_BAD_TYPE;

        types.push_back(t);
    }
    return 0;
}

int SignalSheet::parse_data(const string &line)
{
    vector<string> data_row = parse_line(line);
    string key = "";
    for (const auto &k : key_names) {
        if (key != "")
            key += "_";
        int i = 0;
        for (const auto &data : data_row) {
            if (k == names[i]) {
                key += data;
                break;
            }
            ++i;
        }
    }
    data[key] = data_row;

    return 0;
}

const vector<string> &SignalSheet::get(const char *key)
{
    map<string, vector<string>>::iterator it;
    return (it = data.find(key)) == data.end() ? empty_vector : it->second;
}

int SignalSheet::attr_type(size_t index)
{
    if (index >= types.size())
        return 0;
    return types[index];
}

string SignalSheet::attr_name(size_t index)
{
    if (index >= names.size())
        return string();
    return names[index];
}

vector<string> SignalSheet::get_keys()
{
    vector<string> keys(data.size());
    int i = 0;
    for (const auto &d : data) {
        keys[i] = d.first;
        ++i;
    }
    return keys;
}

const vector<string> ComplexSheet::empty_vector;
const char *ComplexSheet::empty_str = "";

ComplexSheet::~ComplexSheet()
{
    set<SignalSheet*> pset;
    for (const auto &s : key_sheet)
        pset.insert(s.second);

    for (const auto &p : pset)
        delete p;
}

int ComplexSheet::load()
{
    if (is_loaded)
        return SUCCEED;

    for (const auto &sheet : sheets) {
        string file_name = path + "/" + CSV_FILE_NAME(sheet);
        //SignalSheet signal_sheet(sheet.c_str(), key_names);
        SignalSheet *signal_sheet = new SignalSheet(sheet.c_str(), key_names);

        int ret = signal_sheet->load(file_name.c_str());
        if (ret != SUCCEED) {
            delete signal_sheet;
            return ret;
        }
        
        vector<string> sheet_keys = signal_sheet->get_keys();
        for (const auto &key : sheet_keys)
            key_sheet[key] = signal_sheet;
    }
    is_loaded = true;
    return SUCCEED;
}

const vector<string> &ComplexSheet::get(const char *key)
{
    map<string, SignalSheet*>::iterator it;
    return (it = key_sheet.find(key)) == key_sheet.end() ? empty_vector : it->second->get(key);
}

vector<const char*> ComplexSheet::get_keys()
{
    vector<const char*> keys(key_sheet.size());
    int i = 0;
    for (const auto &k : key_sheet) {
        keys[i] = k.first.c_str();
        ++i;
    }
    return keys;
}

int ComplexSheet::attr_type(const char *key, size_t index)
{
    map<string, SignalSheet*>::iterator it;
    return (it = key_sheet.find(key)) == key_sheet.end() ? 0 : it->second->attr_type(index);
}

int ComplexSheet::key_type()
{
    if (key_names.size() > 1)
        return TYPE_STRING;

    if (key_sheet.size() <= 0)
        return TYPE_UNKNOW;

    map<string, SignalSheet*>::iterator it = key_sheet.begin();
    return it->second->key_type;
}

string ComplexSheet::attr_name(const char *key, size_t index)
{
    map<string, SignalSheet*>::iterator it;
    return (it = key_sheet.find(key)) == key_sheet.end() ? empty_str : it->second->attr_name(index);
}
